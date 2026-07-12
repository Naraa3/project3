import streamlit as st
from utils.theme import apply_theme

apply_theme()

st.set_page_config(
    page_title="TourInsight | Home",
    layout="wide"
)

# ---------- HERO SECTION ----------
st.title("TourInsight")
st.subheader("Explore French cities with tourism and weather insights")

st.write(
    """
    TourInsight is a travel data platform that helps users explore popular cities in France.
    It combines points of interest, weather data, and city analytics to make travel planning easier.
    """
)

st.success("Use the sidebar to start exploring the app.")

st.divider()

# ---------- FEATURE CARDS ----------
st.header("What can you explore?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🗺️ Explore France")
    st.write(
        "Browse points of interest, including hotels and restaurants across French cities using an interactive map."
    )

with col2:
    st.markdown("### 📊 City Analytics")
    st.write(
        "Compare cities using weather trends and current conditions."
    )

with col3:
    st.markdown("### 🌦️ Weather Insights")
    st.write(
        "Check current weather, forecasts, and the best time to visit each city."
    )

st.divider()


# ---------- GET STARTED ----------
st.header("Get Started")

left, right = st.columns(2)

with left:
    st.markdown("### First-time visitor?")
    st.write(
        "Start with **Explore France** to see hotels and restaurants on the map."
    )

with right:
    st.markdown("### Want to compare destinations?")
    st.write(
        "Go to **City Analytics** to compare cities and find the best time to visit."
    )

st.divider()

# ---------- SIMPLE FOOTER ----------
st.caption("TourInsight | France tourism and weather analytics project")