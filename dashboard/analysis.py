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
    px.defaults.template = "plotly_dark"

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
    def trust_label(t):
        if t < 60:
            return "Low Confidence"
        elif t == 60:
            return "Unverified"
        else:
            return "Trusted"

    df["trust_level"] = df["trust_index"].apply(trust_label)
        
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Trust Index distribution")
        fig = px.histogram(
            df, x="trust_index", nbins=10,
            color_discrete_sequence=["#4FC3F7"]
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Final Score by Source (top 20)")
        top = (df.groupby("source_domain")["final_score"]
               .mean().sort_values(ascending=False)
               .head(20).reset_index())
        fig2 = px.bar(
            top,
            x="source_domain",
            y="final_score",
            color="source_domain",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Trust Level Distribution")

    trust_counts = df["trust_level"].value_counts().reset_index()
    trust_counts.columns = ["trust_level", "count"]

    fig3 = px.pie(
        trust_counts,
        names="trust_level",
        values="count",
        color="trust_level",
        color_discrete_map={
            "Trusted": "#4CAF50",
            "Unverified": "#FFC107",
            "Low Confidence": "#F44336"
        }
    )

    st.plotly_chart(fig3, use_container_width=True)


