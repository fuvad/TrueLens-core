import pandas as pd
import streamlit as st
import psycopg2, os
from psycopg2.extras import RealDictCursor
import plotly.express as px

def _conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"), port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"), user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"), cursor_factory=RealDictCursor
    )

def render_analysis():
    st.header("Trust & Bias Analysis")
    with _conn() as c, c.cursor() as cur:
        cur.execute("""
            SELECT a.source_domain, s.trust_index, an.bias_label, an.final_score
            FROM articles a
            JOIN summaries s ON s.article_id=a.id
            JOIN analysis an ON an.article_id=a.id
            WHERE s.trust_index IS NOT NULL
        """)
        rows = cur.fetchall()
    if not rows:
        st.info("No analysis yet.")
        return
    df = pd.DataFrame(rows)
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Trust Index distribution")
        fig = px.histogram(df, x="trust_index")
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Final Score by Source (top 20)")
        top = (df.groupby("source_domain")["final_score"].mean()
               .sort_values(ascending=False).head(20).reset_index())
        fig2 = px.bar(top, x="source_domain", y="final_score")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Bias breakdown")
    bias_counts = df["bias_label"].value_counts().reset_index()
    bias_counts.columns = ["bias_label","count"]
    fig3 = px.pie(bias_counts, names="bias_label", values="count")
    st.plotly_chart(fig3, use_container_width=True)
