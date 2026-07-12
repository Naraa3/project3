import streamlit as st
from utils.theme import apply_theme

st.set_page_config(layout="wide",
    page_title="TourInsight | Home")

apply_theme()


st.header("About TourInsight")

st.write("""
TourInsight is a tourism analytics platform designed to help users explore French cities using
weather and tourism data. The project demonstrates an end-to-end data pipeline, from data collection
to visualization, making travel planning more informative and interactive.
""")

st.divider()

st.subheader("👩‍💻 About the Developer")

st.write("""
Hi, I'm **Wagnara Bautista**, a Data Analytics student passionate about data engineering,
data visualization, and software development.

TourInsight was created as a portfolio project to demonstrate skills in building complete
data solutions using modern analytics tools.
""")
st.write("🎓 Wild Code School – Data Analytics")
st.write("📍 Based in France")


st.divider()

st.subheader("📂 GitHub Repository")

st.write(
    "The complete source code for this project is available on GitHub."
)

st.link_button(
    "View on GitHub",
    "https://github.com/Naraa3/project3.git"
)

st.divider()

st.subheader("📊 Data Sources")

st.markdown("""
This project combines data from multiple public sources:

- 🌍 OpenStreetMap (Hotels and Restaurants)
- 🌤️ Open-Meteo API (Current, Forecast, and Historical Weather)
- 🗺️ Geographic coordinates for French cities
""")

st.divider()

st.subheader("🛠️ Technologies")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
- Python
- Pandas
- SQLAlchemy
- PostgreSQL
- Neon
""")

with col2:
    st.markdown("""
- Apache Airflow
- Streamlit
- Plotly
- Folium
- Docker
""")

st.divider()

st.subheader("🚀 Future Improvements")

st.markdown("""
- Hotel ratings and reviews
- AI travel recommendations
- Real-time events
- User accounts and saved trips
""")

st.divider()

# ---------- SIMPLE FOOTER ----------
st.caption("TourInsight | France tourism and weather analytics project")