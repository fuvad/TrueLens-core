from urllib.parse import urlparse
import os, requests
from core.utils.logger import get_logger

log = get_logger("source_filter")

TRUSTED = {
    # Global
    "bbc.com", "bbc.co.uk", "reuters.com", "apnews.com", "theguardian.com",
    "aljazeera.com", "nytimes.com", "washingtonpost.com", "npr.org",
    "bloomberg.com", "financialtimes.com", "forbes.com", "time.com",
    "abcnews.go.com", "cbsnews.com", "nbcnews.com", "usatoday.com",
    "cnn.com", "theatlantic.com", "vox.com",

    # India
    "thehindu.com", "indiatoday.in", "ndtv.com", "hindustantimes.com",
    "timesofindia.indiatimes.com", "business-standard.com", "livemint.com",
    "scroll.in", "theprint.in", "news18.com",

    # Technology & science
    "techcrunch.com", "wired.com", "scientificamerican.com", "nature.com",
    "newscientist.com"
}

BAD = {
    "theonion.com",              # satire
    "infowars.com",              # conspiracy / misinformation
    "beforeitsnews.com",         # conspiracy
    "worldtruth.tv",             # pseudoscience
    "naturalnews.com",           # health misinformation
    "sputniknews.com",           # propaganda-leaning
    "rt.com",                    # state propaganda
    "yournewswire.com",          # fake news site
    "newsbreakapp.com",          # unreliable aggregation
    "clickbaitnews.example",     # placeholder
    "rumorhub.example"           # placeholder
}  # still useful for quick manual rules

SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SB_API_KEY")

def domain_from_url(url: str) -> str:
    """Extract domain from a URL"""
    try:
        return urlparse(url).netloc.lower().replace("www.","")
    except Exception:
        return ""
    
def check_safe_browsing(url: str) -> bool:
    """Return True if URL is considered safe by Google Safe Browsing API"""
    if not SAFE_BROWSING_API_KEY or not url:
        return True  # if key missing, skip check
    
    endpoint = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    body = {
        "client": {"clientId": "TrueLens-app", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE","SOCIAL_ENGINEERING","UNWANTED_SOFTWARE","POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    try:
        r = requests.post(endpoint, params={"key": SAFE_BROWSING_API_KEY}, json=body, timeout=10)
        data = r.json()
        
        # Google returns a "matches" field only if URL is unsafe
        if data.get("matches"):
            log.warning(f"Unsafe URL flagged by Google Safe Browsing: {url}")
            return False
        return True
    except Exception as e:
        log.error(f"Safe Browsing API failed for {url}: {e}")
        return True  # fail open to avoid blocking everything
    
def reliability_tag(url: str) -> str:
    """Labels a URL’s credibility"""
    d = domain_from_url(url)
    if not d:
        return "unverified"
    
    # 1. Check Google Safe Browsing for malicious URLs
    safe = check_safe_browsing(url)
    if not safe:
        return "bad"

    # 2. Then fall back to internal trust rules
    if d in TRUSTED:
        return "trusted"
    if d in BAD:
        return "bad"
    return "unverified"

def is_source_allowed(url: str) -> bool:
    """Allow all except explicit BAD or flagged by Safe Browsing"""
    d = domain_from_url(url)
    if not d:
        return False
    if d in BAD:
        return False
    if not check_safe_browsing(url):
        return False
    return True