"""LLM wrapper with rate limiting and error handling"""

import time
import re
import random
from typing import List
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage

from core.config import TPM_LIMIT, TPM_SAFETY, RATE_RETRIES, LLM_MAX_TOKENS

class TokenBudget:
    """Rolling 60-second token budget manager for rate limiting"""

    def __init__(self, tpm_limit: int, safety: float = 0.8):
        self.limit = int(tpm_limit * safety)
        self.events: List[List[float]] = []

    def _prune(self) -> None:
        """Remove usage events older than 60 seconds"""
        cutoff = time.time() - 60
        self.events = [e for e in self.events if e[0] > cutoff]

    def used(self) -> int:
        """Calculate total tokens consumed in active window"""
        self._prune()
        return int(sum(e[1] for e in self.events))

    def reserve(self, tokens: int) -> None:
        """Block until tokens fit in window"""
        tokens = min(tokens, self.limit)
        while True:
            self._prune()
            if self.used() + tokens <= self.limit or not self.events:
                break
            wait = max(61 - (time.time() - self.events[0][0]), 1.0)
            print(f"  [budget] {self.used()}/{self.limit} tokens - waiting {wait:.0f}s")
            time.sleep(wait)
        self.events.append([time.time(), tokens])

    def settle(self, estimated: int, actual: int) -> None:
        """Reconcile estimated vs actual usage"""
        if self.events and actual > 0:
            self.events[-1][1] = min(actual, self.limit)

    def penalise(self) -> None:
        """Mark budget as full after rate limit error"""
        self.events.append([time.time(), self.limit])


BUDGET = TokenBudget(TPM_LIMIT, TPM_SAFETY)


class RateLimitedChatGroq(ChatGroq):
    """ChatGroq with embedded rate limiting and retries"""

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        estimated = estimate_messages_tokens(messages) + (self.max_tokens or 512)

        for attempt in range(RATE_RETRIES):
            BUDGET.reserve(estimated)
            try:
                result = super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

                try:
                    usage = (result.llm_output or {}).get("token_usage", {})
                    actual = usage.get("total_tokens", 0)
                    if actual:
                        BUDGET.settle(estimated, int(actual))
                except Exception:
                    pass

                return result

            except Exception as e:
                if not is_rate_limit(e) or attempt == RATE_RETRIES - 1:
                    raise

                BUDGET.penalise()
                wait = parse_retry_after(str(e))
                print(f"  [429] rate limited - waiting {wait:.1f}s (attempt {attempt + 1}/{RATE_RETRIES})")
                time.sleep(wait)

        raise RuntimeError("Exhausted rate-limit retries")


def estimate_tokens(text) -> int:
    """Estimate token count (conservative: 3 chars/token)"""
    return max(1, len(str(text)) // 3)


def estimate_messages_tokens(messages) -> int:
    """Estimate total tokens in message list"""
    total = 0
    for m in messages:
        content = getattr(m, "content", m)
        total += estimate_tokens(content) + 4
        for tc in (getattr(m, "tool_calls", None) or []):
            total += estimate_tokens(tc)
    return total


def parse_retry_after(error_text: str, default: float = 20.0) -> float:
    """Extract recommended backoff duration from API error"""
    m = re.search(r"try again in ([\d.]+)\s*m?s", error_text, re.I)
    if m:
        secs = float(m.group(1))
        if "ms" in error_text[m.start():m.end() + 3].lower():
            secs /= 1000.0
        return secs + 2.0

    m = re.search(r"try again in (\d+)m([\d.]+)s", error_text, re.I)
    if m:
        return float(m.group(1)) * 60 + float(m.group(2)) + 2.0

    return default


def is_rate_limit(err: Exception) -> bool:
    """Check if exception is a rate limit error"""
    msg = str(err).lower()
    return any(k in msg for k in ["rate limit", "rate_limit", "429", "too many requests"])


def clip(text: str, n: int) -> str:
    """Collapse whitespace and truncate text"""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:n]


def safe_llm_call(messages, model=None, retries: int = 3) -> str:
    """Call LLM with retry logic for transient failures"""
    model = model or None

    for attempt in range(retries):
        try:
            if model is None:
                from core.config import MODEL_NAME
                import os
                llm = RateLimitedChatGroq(
                    model=MODEL_NAME,
                    temperature=0,
                    max_tokens=LLM_MAX_TOKENS,
                    max_retries=0,
                    groq_api_key=os.environ.get("GROQ_API_KEY", ""),
                )
            else:
                llm = model

            return llm.invoke(messages).content

        except Exception as e:
            msg = str(e).lower()
            transient = any(k in msg for k in ["timeout", "overloaded", "503", "502", "connection", "rate limit"])
            if not transient or attempt == retries - 1:
                print(f"  [LLM error] {e}")
                return ""

            wait = 5.0 * (2 ** attempt) + random.uniform(0, 2)
            print(f"  [retry {attempt + 1}/{retries}] {type(e).__name__} - waiting {wait:.1f}s")
            time.sleep(wait)

    return ""
