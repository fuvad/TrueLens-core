import streamlit as st
from pages.feed import render_feed
from pages.analysis import render_analysis
from pages.insights import render_insights
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="SenseAI", layout="wide")
st.sidebar.title("SenseAI")
page = st.sidebar.radio("Navigate", ["Feed","Analysis","Insights"])

if page=="Feed":
    render_feed()
elif page=="Analysis":
    render_analysis()
else:
    render_insights()
