from urllib.parse import urlparse
import os, requests
from core.utils.logger import get_logger

log = get_logger("source_filter")

TRUSTED = {
    # 🌍 Global News
    "bbc.com", "reuters.com", "apnews.com", "theguardian.com", "aljazeera.com",
    "nytimes.com", "washingtonpost.com", "npr.org", "bloomberg.com", "financialtimes.com",
    "forbes.com", "time.com", "economist.com", "newsweek.com", "thetimes.co.uk", "telegraph.co.uk",
    "cbc.ca", "abc.net.au", "lemonde.fr", "elpais.com", "asahi.com", "dw.com",
    "japantimes.co.jp", "spiegel.de", "smh.com.au",

    # 🇮🇳 India News
    "thehindu.com", "timesofindia.indiatimes.com", "hindustantimes.com", "indiatoday.in",
    "ndtv.com", "scroll.in", "livemint.com", "theprint.in", "news18.com", "thewire.in",
    "telegraphindia.com", "deccanherald.com", "dailyo.in", "indianexpress.com", "zeenews.india.com",
    "telecom.economictimes.indiatimes.com", "firstpost.com", "outlookindia.com", "thequint.com", "greaterkashmir.com",

    # 🧠 Technology & Science
    "techcrunch.com", "wired.com", "verge.com", "arstechnica.com", "thenextweb.com",
    "engadget.com", "gizmodo.com", "mashable.com", "scientificamerican.com", "nature.com",
    "newscientist.com", "quantamagazine.org", "cerncourier.com", "popularscience.com",
    "technologyreview.com", "ieee.org", "sciencedaily.com", "science.org", "space.com", "techradar.com",

    # 🏆 Sports
    "espn.com", "bbc.com/sport", "sky.com/sports", "foxsports.com", "cbssports.com",
    "bleacherreport.com", "theathletic.com", "goal.com", "marca.com", "livescore.com",
    "cricbuzz.com", "icc-cricket.com", "nba.com", "uefa.com", "olympics.com",

    # 🗳️ Politics & Policy
    "politico.com", "thehill.com", "foreignpolicy.com", "nationalreview.com", "slate.com",
    "vox.com", "theatlantic.com", "pjmedia.com", "realclearpolitics.com", "brookings.edu",
    "cfr.org", "heritage.org", "amnesty.org", "hrw.org", "pewresearch.org",
    "rand.org", "csis.org", "chathamhouse.org", "aei.org", "foreignaffairs.com"
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