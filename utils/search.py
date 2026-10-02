"""DuckDuckGo search with retry logic"""

import json
import re
from typing import List, Dict, Any, Optional
from ddgs import DDGS
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.config import MAX_RESULTS_PER_QUERY, MAX_BODY_CHARS

SEARCH_CACHE: Dict[str, Dict[str, str]] = {}

def clip(text: str, n: int) -> str:
    """Collapse whitespace and truncate"""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:n]

def _normalise(r: dict) -> Optional[Dict[str, str]]:
    """Normalize search result dictionary"""
    url = r.get("href") or r.get("url") or r.get("link") or ""
    if not url:
        return None
    
    title = clip(r.get("title", ""), 100)
    body = clip(r.get("body") or r.get("excerpt") or "", MAX_BODY_CHARS)
    date = str(r.get("date", ""))[:10]
    
    return {"title": title, "url": url, "body": body, "date": date}

@retry(
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception)
)
def ddg_search(query: str) -> str:
    """Search DuckDuckGo News with retry logic"""
    query = clip(query, 200)
    results: List[Dict[str, str]] = []
    
    try:
        with DDGS() as ddgs:
            try:
                raw = list(ddgs.news(query, max_results=MAX_RESULTS_PER_QUERY))
            except Exception:
                raw = []
            
            if not raw:
                raw = list(ddgs.text(query, max_results=MAX_RESULTS_PER_QUERY))
        
        for r in raw:
            item = _normalise(r)
            if item:
                results.append(item)
                SEARCH_CACHE[item["url"]] = item
    
    except Exception as e:
        print(f"  [search failed] {query[:50]!r}: {type(e).__name__}")
        return json.dumps([])
    
    return json.dumps(results, ensure_ascii=False)
