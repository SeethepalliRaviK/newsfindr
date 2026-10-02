"""Google News RSS search with retry logic"""

import re
from typing import List, Dict
import feedparser
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
    """Search Google News RSS for actual news articles"""
    query = clip(query, 200)
    results: List[Dict[str, str]] = []

    try:
        # Google News RSS feed for search query
        url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}"

        feed = feedparser.parse(url)

        if not feed.entries:
            print(f"  [news search] No results found for: {query[:40]}")
            return []

        # Process feed entries
        for entry in feed.entries[:MAX_RESULTS_PER_QUERY * 2]:
            try:
                title = entry.get('title', '')
                link = entry.get('link', '')
                summary = entry.get('summary', '')
                published = entry.get('published', '')

                if not (title and link):
                    continue

                # Extract date from published timestamp
                date = published[:10] if published else ''

                # Clean summary (remove HTML tags)
                summary_clean = re.sub(r'<[^>]+>', '', summary)

                result = {
                    'title': clip(title, 100),
                    'url': clip(link, 300),
                    'body': clip(summary_clean, MAX_BODY_CHARS),
                    'date': date
                }

                results.append(result)
                SEARCH_CACHE[result['url']] = result

                if len(results) >= MAX_RESULTS_PER_QUERY:
                    break

            except Exception as e:
                continue

        if results:
            print(f"  [news search] Found {len(results)} articles for: {query[:40]}")
        else:
            print(f"  [news search] No valid entries for: {query[:40]}")

    except Exception as e:
        print(f"  [ddg_search failed] {query[:40]!r}: {type(e).__name__}")
        return []

    return results
