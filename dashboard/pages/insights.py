import streamlit as st
import pandas as pd
import psycopg2, os
from psycopg2.extras import RealDictCursor

def _conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"), cursor_factory=RealDictCursor
    )

def render_insights():
    st.header("Insights")
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT source_domain,
                   COUNT(*) AS articles,
                   AVG(COALESCE(s.trust_index,0)) AS avg_trust,
                   AVG(COALESCE(an.final_score,0)) AS avg_final
            FROM articles a
            LEFT JOIN summaries s ON s.article_id=a.id
            LEFT JOIN analysis an ON an.article_id=a.id
            GROUP BY source_domain
            ORDER BY avg_final DESC NULLS LAST
            LIMIT 50
        """)
        rows = cur.fetchall()
    if not rows:
        st.info("No data yet.")
        return
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
