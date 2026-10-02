"""Text formatting and filtering utilities"""

import json
import re
from typing import List, Dict, Any, Optional
from utils.search import SEARCH_CACHE, clip
from utils.llm import safe_llm_call
from langchain_core.messages import SystemMessage, HumanMessage

def _coerce_results(search_results: Any) -> List[Dict[str, Any]]:
    """Convert various formats to list of dicts"""
    if isinstance(search_results, list):
        out = []
        for r in search_results:
            if isinstance(r, dict):
                out.append(r)
            elif isinstance(r, str):
                out.extend(_coerce_results(r))
        return out
    
    if isinstance(search_results, dict):
        for key in ("results", "items", "sources", "data", "search_results"):
            if key in search_results and isinstance(search_results[key], (list, str)):
                return _coerce_results(search_results[key])
        return [search_results] if search_results.get("url") else []
    
    if isinstance(search_results, str):
        items: List[Dict[str, Any]] = []
        for blob in re.findall(r"\[.*?\]", search_results, re.S):
            try:
                parsed = json.loads(blob)
                items.extend(r for r in parsed if isinstance(r, dict))
            except json.JSONDecodeError:
                continue
        
        if items:
            return items
        
        return [SEARCH_CACHE.get(u, {"title": "", "url": u, "body": ""})
                for u in re.findall(r"https?://\S+", search_results)]
    
    return []

def _enrich(record: Dict[str, Any]) -> Dict[str, str]:
    """Restore cached content for URL"""
    url = str(record.get("url", "")).strip().rstrip('.,)"\'')
    cached = SEARCH_CACHE.get(url, {})
    
    return {
        "title": clip(record.get("title") or cached.get("title", ""), 90),
        "url": url,
        "body": clip(record.get("body") or cached.get("body", ""), 1000),
    }

def filter_with_llm(results: Any) -> str:
    """Filter news sources by credibility"""
    items = [_enrich(r) for r in _coerce_results(results) if r.get("url")]
    
    if not items:
        return json.dumps([])
    
    seen, deduped = set(), []
    for r in items:
        domain = re.sub(r"^https?://(www\.)?", "", r["url"]).split("/")[0].lower()
        if domain and domain not in seen:
            seen.add(domain)
            deduped.append(r)
    
    deduped = deduped[:8]
    
    numbered = "\n".join(
        f"{i}. {r['title']} | {r['url']}" for i, r in enumerate(deduped)
    )
    
    system_prompt = "You are a news credibility filter. Identify credible, relevant sources. Return 0-indexed numbers as JSON array. No commentary."
    
    raw = safe_llm_call([SystemMessage(content=system_prompt),
                         HumanMessage(content=numbered)])
    
    kept = []
    match = re.search(r"\[[^\]]*\]", raw, re.S)
    if match:
        try:
            for n in json.loads(match.group(0)):
                if isinstance(n, int) and 0 <= n < len(deduped):
                    kept.append(deduped[n])
        except (json.JSONDecodeError, TypeError):
            pass
    
    if not kept:
        kept = deduped[:4]
    
    return json.dumps(kept[:4], ensure_ascii=False)

def summarize_news(sources: Any) -> str:
    """Summarize credible news sources"""
    items = [_enrich(r) for r in _coerce_results(sources) if r.get("url")]
    items = items[:4]
    
    if not items:
        return "No credible sources available."
    
    urls = [r["url"] for r in items]
    lines = [f"{i}. TITLE: {r['title'] or '(none)'}\n   URL: {r['url']}\n   SNIPPET: {r['body'] or '(none)'}"
             for i, r in enumerate(items, 1)]
    have_content = any(r["title"] or r["body"] for r in items)
    
    system_prompt = "You are a news summarizer. Create a concise, neutral briefing from sources. Don't add external info."
    if not have_content:
        system_prompt += "\nNo snippets available - write brief outlet descriptions instead."
    
    prompt = "Sources to summarize:\n" + "\n".join(lines)
    
    summary = safe_llm_call([SystemMessage(content=system_prompt),
                             HumanMessage(content=prompt)])
    
    if not summary or re.search(r"(could you|can you|please provide|I can't create)", summary[:300], re.I):
        summary = "Headlines:\n" + "\n".join(f"- {r['title'] or r['url']}: {r['body']}" for r in items)
    
    return summary + "\n\nSources:\n" + "\n".join(f"- {u}" for u in urls)
