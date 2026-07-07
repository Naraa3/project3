import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Explore France | TourInsight",
    layout="wide"
)

# Connection with Neon DB
DATABASE_URL = "postgresql://neondb_owner:npg_MBG4insD6VQe@ep-old-recipe-atuuayxa-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
engine = create_engine(DATABASE_URL)

@st.cache_data
def load_data():
    query = "SELECT * FROM dim_poi"
    return pd.read_sql(query, engine)

df = load_data()

@st.cache_data
def load_weather():
    query = "SELECT * FROM weather_current"
    return pd.read_sql(query, engine)

weather_df = load_weather()


st.title("Explore France")
st.write("Explore Hotels and Restaurants across major French cities")

# Sidebar filters
st.sidebar.header("Filters")

cities = sorted(df["city"].unique())
selected_city = st.sidebar.selectbox("Choose a city", cities)

city_weather = weather_df[weather_df["city"] == selected_city]

categories = sorted(df["category"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Choose categories",
    categories,
    default=categories
)

search = st.sidebar.text_input("Search by name")

# Filter data
filtered_df = df[
    (df["city"] == selected_city) &
    (df["category"].isin(selected_categories))
]

if search:
    filtered_df = filtered_df[
        filtered_df["name"].str.contains(search, case=False, na=False)
    ]

# Amounts
col1, col2, col3 = st.columns(3)

col1.metric("🏨 Hotels", len(filtered_df[filtered_df["category"] == "hotel"]))
col2.metric("🍽 Restaurants", len(filtered_df[filtered_df["category"] == "restaurant"]))

if not city_weather.empty:
    temp = city_weather.iloc[0]["temperature_c"]
    col3.metric("🌤 Temperature", f"{temp}°C")
else:
    col3.metric("🌤 Temperature", "N/A")

st.divider()

# Map
st.subheader(f"Map of {selected_city}")

map_df = filtered_df.dropna(subset=["lat", "lon"])

# Limit map points for performance, but use clustering
if len(map_df) > 1000:
    map_df = map_df.sample(1000, random_state=42)

if len(map_df) > 0:
    center_lat = map_df["lat"].mean()
    center_lon = map_df["lon"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="CartoDB dark_matter"
    )

    marker_cluster = MarkerCluster().add_to(m)

    for _, row in map_df.iterrows():
        color = "blue" if row["category"] == "hotel" else "red"
        icon = "home" if row["category"] == "hotel" else "cutlery"

        address = row["address"] if pd.notna(row["address"]) and row["address"] != "" else "Address not available"

        popup_html = f"""
        <b>{row['name']}</b><br>
        Category: {row['category']}<br>
        Address: {address}<br>
        """

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row["name"],
            icon=folium.Icon(color=color, icon=icon, prefix="fa")
        ).add_to(marker_cluster)

    st_folium(m, width=1100, height=550)

else:
    st.warning("No map data available for this selection.")

st.divider()

# Table
st.subheader("Results")

table_df = filtered_df.copy()

table_df["address"] = table_df["address"].fillna("—")

table_df = table_df.rename(columns={
    "name": "Name",
    "category": "Category",
    "address": "Address",
    "city": "City"
})

st.dataframe(
    table_df[["Name", "Category", "Address", "City"]],
    use_container_width=True
)