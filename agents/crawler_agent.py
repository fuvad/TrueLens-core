"""
Fetches news via NewsData.io, validates sources, fills missing text via Firecrawl.
Supports pagination and safely respects API rate limits.
"""

import os, time, requests
from datetime import datetime, timezone
from tenacity import retry, stop_after_attempt, wait_exponential
from core.utils.source_filter import is_source_allowed, reliability_tag
from core.utils.logger import get_logger
from dotenv import load_dotenv

load_dotenv()
log = get_logger("crawler")

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# -----------------------------------------------
# Internal helper for API requests
# -----------------------------------------------
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def _newsdata_request(params):
    print("Requesting NewsData.io with params:", params)
    resp = requests.get("https://newsdata.io/api/1/news", params=params, timeout=20)
    print("Status code:", resp.status_code)
    print("Response text:", resp.text[:500])
    resp.raise_for_status()
    return resp.json()

# -----------------------------------------------
# Extract article text using Firecrawl
# -----------------------------------------------
def extract_text_firecrawl(url: str) -> str:
    if not url:
        return ""
    try:
        r = requests.post(
            "https://api.firecrawl.dev/v1/extract",
            headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"},
            json={"url": url},
            timeout=30
        )
        return r.json().get("text", "") if r.ok else ""
    except Exception as e:
        log.warning(f"Firecrawl failed: {e}")
        return ""

# -----------------------------------------------
# Fetch paginated news results
# -----------------------------------------------
def fetch_news(topic: str = "latest", limit: int = 20, countries: str = "us,in,gb"):
    if not NEWSDATA_API_KEY:
        log.error("NEWSDATA_API_KEY missing")
        return []

    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": topic,
        "language": "en",
        "country": countries
    }

    out = []
    next_page = None

    try:
        while len(out) < limit:
            if next_page:
                params["page"] = next_page  # use token, not numeric page
            data = _newsdata_request(params)

            if data.get("status") != "success":
                log.error(f"NewsData returned error: {data}")
                break

            results = data.get("results") or []
            if not results:
                break

            for a in results:
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
                    published = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else datetime.now(timezone.utc)
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
                    "is_verified": True if tag == "trusted" else None
                })

                if len(out) >= limit:
                    break

            next_page = data.get("nextPage")
            if not next_page:
                break  # no more pages

            time.sleep(1.5)  # avoid rate-limit issues

    except Exception as e:
        log.error(f"NewsData error: {e}")
        return []

    log.info(f"Fetched {len(out)} articles for topic='{topic}'")
    return out

# -----------------------------------------------
# Standalone test
# -----------------------------------------------
if __name__ == "__main__":
    for art in fetch_news("ai", limit=15):
        log.info(f"{art['source_domain']} | {art['reliability_tag']} | {art['title']}")
