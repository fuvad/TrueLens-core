import argparse, os     #argparse → lets you run the script with command-line arguments like --topic ai --limit 20
from datetime import datetime
from core.utils.logger import get_logger
from agents.crawler_agent import fetch_news
from agents.summarizer_agent import summarize
from agents.analyzer_agent import analyze_bias
from core.utils.db_connect import exec_one
from dotenv import load_dotenv
load_dotenv()

log = get_logger("pipeline")

def upsert_source(domain, tag):
    exec_one("""
        INSERT INTO sources(domain, reliability_tag, last_seen)
        VALUES (%s,%s,NOW())
        ON CONFLICT(domain) DO UPDATE SET
          reliability_tag=EXCLUDED.reliability_tag,
          last_seen=NOW()
    """, (domain, tag))
    
def insert_article(a):
    exec_one("""
        INSERT INTO articles(title, url, source_domain, summary, content, published_at, is_verified)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (url) DO NOTHING
    """, (a["title"], a["url"], a["source_domain"], a["summary"], a["content"], a["published_at"], a["is_verified"]))
    
    rows = exec_one("SELECT id FROM articles WHERE url=%s", (a["url"],))
    return rows[0]["id"] if rows else None

def insert_summary(article_id, s):
    exec_one("""
        INSERT INTO summaries(article_id, neutral_summary, trust_index, reasoning)
        VALUES (%s,%s,%s,%s)
    """, (article_id, s["neutral_summary"], s["trust_index"], s["reasoning"]))
    
def insert_analysis(article_id, an):
    """Insert bias analysis results with computed final score"""
    exec_one("""
        INSERT INTO analysis(article_id, bias_label, bias_score, final_score)
        VALUES (%s,%s,%s,%s)
    """, (article_id, an["bias_label"], an["bias_score"], an["final_score"]))
        
# -------------------------------
# Pipeline logic
# -------------------------------

def run(topic: str, limit: int):
    """Fetch, summarize, analyze, and store articles."""
    arts = fetch_news(topic=topic, limit=limit)
    saved = 0
    
    for a in arts:
        upsert_source(a["source_domain"], a["reliability_tag"])
        article_id = insert_article(a)
        if not article_id:
            continue  # Skip duplicates

        # Summarize content
        s = summarize(a["content"], a["reliability_tag"])
        insert_summary(article_id, s)

        # Analyze bias and compute final trust score
        an = analyze_bias(a["content"] or a["summary"])
        penalty = int(abs(an["bias_score"]) * 30)
        final_score = max(0, min(100, s["trust_index"] - penalty))
        an["final_score"] = final_score

        insert_analysis(article_id, an)
        saved += 1
        
    log.info(f"✅ Ingested {saved}/{len(arts)} articles")
    
# -------------------------------
# CLI entry point
# -------------------------------
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--topic", default="latest", help="Topic to fetch news for")
    p.add_argument("--limit", type=int, default=20, help="Number of articles to process")
    args = p.parse_args()

    run(args.topic, args.limit)
        