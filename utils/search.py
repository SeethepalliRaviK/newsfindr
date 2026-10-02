"""DuckDuckGo search with retry logic and fallback"""

import re
from typing import List, Dict
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from core.config import MAX_RESULTS_PER_QUERY, MAX_BODY_CHARS

SEARCH_CACHE: Dict[str, Dict[str, str]] = {}

def clip(text: str, n: int) -> str:
    """Collapse whitespace and truncate"""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:n]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    retry=retry_if_exception_type(Exception)
)
def ddg_search(query: str) -> List[Dict[str, str]]:
    """Search DuckDuckGo using direct HTTP API"""
    query = clip(query, 200)
    results: List[Dict[str, str]] = []

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Try DuckDuckGo instant answer API
        url = "https://api.duckduckgo.com/"
        params = {
            'q': query,
            'format': 'json',
            'no_redirect': '1',
            'no_html': '1',
            'skip_disambig': '1'
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Extract results from different sections
        raw_results = []

        # Get results from different DuckDuckGo response fields
        if data.get('Results'):
            raw_results.extend(data.get('Results', []))

        if data.get('RelatedTopics'):
            raw_results.extend(data.get('RelatedTopics', []))

        # Process results
        seen_urls = set()
        for item in raw_results[:MAX_RESULTS_PER_QUERY * 2]:
            if not isinstance(item, dict):
                continue

            try:
                title = item.get('Title', item.get('Text', ''))
                url_val = item.get('URL', item.get('FirstURL', ''))
                body = item.get('Text', title)

                # Skip if no URL or title
                if not (title and url_val):
                    continue

                # Skip duplicates
                if url_val in seen_urls:
                    continue

                seen_urls.add(url_val)

                result = {
                    'title': clip(title, 100),
                    'url': clip(url_val, 300),
                    'body': clip(body, MAX_BODY_CHARS),
                    'date': ''
                }

                results.append(result)
                SEARCH_CACHE[result['url']] = result

                if len(results) >= MAX_RESULTS_PER_QUERY:
                    break

            except Exception as e:
                continue

    except Exception as e:
        print(f"  [ddg_search failed] {query[:40]!r}: {type(e).__name__}")
        return []

    return results
