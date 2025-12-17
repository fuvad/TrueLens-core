import pandas as pd
import streamlit as st
import psycopg2, os, time
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
load_dotenv()


def _conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        cursor_factory=RealDictCursor
    )

def render_feed():
    st.header("Live Article Feed")
    topic = st.text_input("Search topic", value="latest")
    limit = st.slider("Limit", 10, 100, 30)

    if st.button("Fetch & Analyze"):
        import subprocess, sys
        with st.spinner("Fetching and analyzing articles... this may take a moment ⏳"):
            cmd = [sys.executable, "-m", "core.pipeline", "--topic", topic, "--limit", str(limit)]
            subprocess.run(cmd, check=False)

        st.success("✅ Pipeline completed. Refreshing feed...")
        time.sleep(5)  # Give DB time to commit inserts
        st.rerun()  # Auto-refresh dashboard to show new articles

    # Fetch and display articles from DB
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT a.title, a.url, a.source_domain,
                   s.trust_index, an.bias_label, an.final_score, a.published_at
            FROM articles a
            LEFT JOIN summaries s ON s.article_id = a.id
            LEFT JOIN analysis an ON an.article_id = a.id
            ORDER BY a.published_at DESC NULLS LAST
            LIMIT 200
        """)
        rows = cur.fetchall()

    if not rows:
        st.info("No articles yet. Click Fetch & Analyze to start collecting.")
        return

    df = pd.DataFrame(rows)
    def trust_label(t):
        if t < 60:
            return "Low Confidence"
        elif t == 60:
            return "Unverified"
        else:
            return "Trusted"
    df["trust_level"] = df["trust_index"].apply(trust_label)
    st.dataframe(df, use_container_width=True, hide_index=True)
