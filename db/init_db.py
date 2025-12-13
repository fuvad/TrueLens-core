"""
init_db.py
Handles insertion of enriched articles into PostgreSQL.
Receives articles from pipeline.py and saves them to:
- articles
- summaries
- analysis
"""

from core.utils.db_connect import execute_query, get_db_connection
from psycopg2 import sql

# ---------------------------
# SAVE ARTICLE FUNCTION
# ---------------------------
def save_article(article: dict):
    """
    Save a processed article dictionary into the database.
    Handles:
    - duplicate URLs
    - foreign key insertion
    - all three tables (articles, summaries, analysis)
    """
    # Extract fields from article dict
    title = article.get("title", "Untitled")
    url = article.get("url")
    source_domain = article.get("source_domain", "unknown")
    published_at = article.get("published_at")
    
    neutral_summary = article.get("neutral_summary", "")
    trust_index = article.get("trust_index", 50)
    reasoning = article.get("reasoning", "")
    
    bias_label = article.get("bias_label", "unknown")
    bias_score = article.get("bias_score", 0.0)
    final_score = article.get("final_score", 0.0)
    
    # ---------------------------
    # Step 1: Check if article exists
    # ---------------------------
    exists_query = "SELECT id FROM articles WHERE url = %s;"
    existing = execute_query(exists_query, (url,), fetch=True)
    
    if existing:
        print(f"⚠️ Article already exists in DB: {url}")
        return existing[0]["id"]
    
    # ---------------------------
    # Step 2: Insert into articles
    # ---------------------------
    insert_article_query = """
    INSERT INTO articles (title, url, source_domain, published_at)
    VALUES (%s, %s, %s, %s)
    RETURNING id;
    """
    
    article_id = None
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(insert_article_query, (title, url, source_domain, published_at))
                article_id = cur.fetchone()[0]
                
                # ---------------------------
                # Step 3: Insert into summaries
                # ---------------------------
                insert_summary_query = """
                INSERT INTO summaries (article_id, neutral_summary, trust_index, reasoning)
                VALUES (%s, %s, %s, %s);
                """
                cur.execute(insert_summary_query, (article_id, neutral_summary, trust_index, reasoning))
                
                # ---------------------------
                # Step 4: Insert into analysis
                # ---------------------------
                insert_analysis_query = """
                INSERT INTO analysis (article_id, bias_label, bias_score, final_score)
                VALUES (%s, %s, %s, %s);
                """
                cur.execute(insert_analysis_query, (article_id, bias_label, bias_score, final_score))
                
                print(f"✅ Saved article: {url} (id={article_id})")
    except Exception as e:
        print(f"❌ Error saving article: {url}")
        print(e)
    finally:
        conn.close()
    
    return article_id


# ---------------------------
# TEST FUNCTION (OPTIONAL)
# ---------------------------
if __name__ == "__main__":
    # Example article dict for local testing
    test_article = {
        "title": "Example Article",
        "url": "https://example.com/news/123",
        "source_domain": "example.com",
        "published_at": "2025-12-13 12:00:00",
        "neutral_summary": "This is a neutral summary.",
        "trust_index": 85,
        "reasoning": "Well-sourced and factual.",
        "bias_label": "neutral",
        "bias_score": 0.0,
        "final_score": 85
    }
    
    save_article(test_article)
