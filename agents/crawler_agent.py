"""
Fetches news via NewsData.io, validates sources, fills missing text via Firecrawl.
"""

import os, requests
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential
from core.utils.source_filter import is_source_allowed, reliability_tag
from core.utils.logger import get_logger
from dotenv import load_dotenv
load_dotenv()

log = get_logger("crawler")

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _newsdata_request(params):      #For Internal Use
    resp = requests.get("https://newsdata.io/api/1/news", params=params, timeout=20)
    resp.raise_for_status()     #If the server returns an error, this line raises an exception
    return resp.json()      #Converts the API’s JSON response into a Python dictionary and returns it

def extract_text_firecrawl(url: str) -> str:
    if not url: return ""
    try:
        r = requests.post(
            "https://api.firecrawl.dev/v1/extract",
            headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
            json={"url": url}, timeout=30
        )
        return r.json().get("text","") if r.ok else ""
    except Exception as e:
        log.warning(f"Firecrawl failed: {e}")
        return ""
    
def fetch_news(topic: str="latest", limit: int=20, countries="us,in,gb"):
    if not NEWSDATA_API_KEY:
        log.error("NEWSDATA_API_KEY missing")
        return []
    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": topic,
        "language": "en",
        "country": countries
    }
    
    try:
        data = _newsdata_request(params)
        
    except Exception as e:
        log.error(f"NewsData error: {e}")
        return []
    
    out = []
    for a in (data.get("results") or [])[:limit]:
        url = a.get("source_url") or a.get("link") or ""
        if not is_source_allowed(url):
            continue
        tag = reliability_tag(url)
        title = a.get("title") or "Untitled"
        summary = a.get("description") or ""
        content = a.get("content") or summary
        if not content:
            content = extract_text_firecrawl(url)
            
        published = a.get("pubDate")
        
        try:
            published = datetime.fromisoformat(published.replace("Z","+00:00")) if published else datetime.now(timezone.utc)
            
        except Exception:
            published = datetime.now(timezone.utc)

        out.append({
            "title": title,
            "url": url,
            "source_domain": url.split("/")[2] if "://" in url else url,
            "summary": summary,
            "content": content,
            "published_at": published.isoformat(),
            "reliability_tag": tag,
            "is_verified": True if tag=="trusted" else None
        })
        
    log.info(f"Fetched {len(out)} articles for topic='{topic}'")
    return out
    
if __name__ == "__main__":
    for art in fetch_news("ai", limit=5):
        log.info(f"{art['source_domain']} | {art['reliability_tag']} | {art['title']}")
    
    