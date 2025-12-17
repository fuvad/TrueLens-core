import streamlit as st
from feed import render_feed
from analysis import render_analysis
from insights import render_insights
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="TrueLens", layout="wide")

st.sidebar.title("TrueLens")

page = st.sidebar.radio(
    "Navigate",
    ["Feed", "Analysis", "Insights"]
)

if page == "Feed":
    render_feed()
elif page == "Analysis":
    render_analysis()
else:
    render_insights()
