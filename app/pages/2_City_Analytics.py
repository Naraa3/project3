from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_theme

apply_theme()

st.set_page_config(page_title="TourInsight | City Analytics", layout="wide")

load_dotenv()
@st.cache_resource
def get_engine():
    return create_engine(os.getenv("DATABASE_URL"))

engine = get_engine()

@st.cache_data(ttl=3600)
def load_data():
    current = pd.read_sql("SELECT * FROM weather_current", engine)
    forecast = pd.read_sql("SELECT * FROM weather_forecast", engine)
    forecast["forecast_date"] = pd.to_datetime(forecast["forecast_date"])
    return current, forecast

try:
    current_df, forecast_df = load_data()
except Exception as e:
    st.error("Could not load weather data from the database.")
    st.exception()
    st.stop()

import plotly.express as px

st.header("Best Time to Visit")

st.divider()

# City list from weather data
cities = sorted(current_df["city"].dropna().unique())

selected_city = st.selectbox(
    "Select a city",
    cities
)

@st.cache_data(ttl=3600)
def load_poi():
    return pd.read_sql("SELECT * FROM dim_poi", engine)

df = load_poi()

@st.cache_data(ttl=3600)
def load_historical():
    return pd.read_sql("SELECT * FROM weather_historical_monthly", engine)

historical_df = load_historical()

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

city_hist = historical_df[historical_df["city"] == selected_city].sort_values("month")
city_hist["month_name"] = city_hist["month"].apply(lambda m: MONTH_NAMES[m - 1])

fig_seasonality = px.line(
    city_hist, x="month_name", y=["avg_temp_max", "avg_temp_min"],
    labels={"value": "Avg Temperature (°C)", "month_name": "Month", "variable": "Metric"},
    markers=True, title=f"{selected_city} — Average Temperature by Month (3-year avg)"
)
st.plotly_chart(fig_seasonality, use_container_width=True)

fig_precip_season = px.bar(
    city_hist, x="month_name", y="avg_precip",
    labels={"avg_precip": "Avg Precipitation (mm)", "month_name": "Month"},
    title=f"{selected_city} — Average Precipitation by Month"
)
st.plotly_chart(fig_precip_season, use_container_width=True)

# Simple "best month" heuristic: warmest month with below-median rain
best_row = city_hist[city_hist["avg_precip"] <= city_hist["avg_precip"].median()].sort_values("avg_temp_max", ascending=False).iloc[0]
st.success(f"☀️ Best time to visit **{selected_city}**: **{best_row['month_name']}** (avg {best_row['avg_temp_max']}°C, {best_row['avg_precip']}mm rain)")

st.divider()
st.subheader("⚖️ Compare Cities")

compare_cities = st.multiselect(
    "Select 2-3 cities to compare", cities,
    default=cities[:2], max_selections=3
)

if len(compare_cities) >= 2:
    compare_current = current_df[current_df["city"].isin(compare_cities)].sort_values("temperature_c")
    fig_compare_temp = px.bar(
        compare_current, x="temperature_c", y="city", orientation="h",
        color="temperature_c", color_continuous_scale="RdYlBu_r",
        text="temperature_c",
        labels={"temperature_c": "Current Temperature (°C)", "city": "City"},
        title="Current Temperature Comparison"
    )
    fig_compare_temp.update_traces(texttemplate="%{text:.1f}°C", textposition="outside")
    fig_compare_temp.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_compare_temp, use_container_width=True)

    compare_hist = historical_df[historical_df["city"].isin(compare_cities)].sort_values("month")
    compare_hist["month_name"] = compare_hist["month"].apply(lambda m: MONTH_NAMES[m - 1])

    fig_compare_season = px.line(
        compare_hist, x="month_name", y="avg_temp_max", color="city",
        labels={"avg_temp_max": "Avg Max Temp (°C)", "month_name": "Month"},
        markers=True, title="Seasonality Comparison"
    )
    st.plotly_chart(fig_compare_season, use_container_width=True)

    compare_poi = df[df["city"].isin(compare_cities)].groupby(["city", "category"]).size().reset_index(name="count")
    fig_compare_poi = px.bar(
        compare_poi, x="city", y="count", color="category", barmode="group",
        title="POI Count Comparison"
    )
    st.plotly_chart(fig_compare_poi, use_container_width=True)
else:
    st.info("Select at least 2 cities to compare.")

st.divider()

# ---------- SIMPLE FOOTER ----------
st.caption("TourInsight | France tourism and weather analytics project")