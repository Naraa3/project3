import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import openrouteservice
from dotenv import load_dotenv
import os


st.set_page_config(
    page_title="Explore France | TourInsight",
    layout="wide"
)

# Connection with Neon DB and OpenRouteService API
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ORS_API_KEY = os.getenv("ORS_API_KEY")

engine = create_engine(DATABASE_URL)
ors_client = openrouteservice.Client(key=ORS_API_KEY)


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
st.write("Find Hotels and Restaurants across major French cities")

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

# Directions section to Google maps
st.subheader("Get Directions")

destination_options = filtered_df.dropna(subset=["lat", "lon"]).copy()

if len(destination_options) > 0:
    destination_options["display_name"] = (
        destination_options["name"].fillna("Unknown")
        + " - "
        + destination_options["category"].fillna("")
        + " - "
        + destination_options["city"].fillna("")
    )

    origin = st.text_input(
        "Enter your starting point",
        placeholder="Example: Lyon Part-Dieu, Paris Gare du Nord..."
    )

    selected_destination = st.selectbox(
        "Choose a destination",
        destination_options["display_name"]
    )

    destination_row = destination_options[
        destination_options["display_name"] == selected_destination
    ].iloc[0]

    destination_lat = destination_row["lat"]
    destination_lon = destination_row["lon"]

    travel_mode = st.selectbox(
        "Travel mode",
        ["Driving", "Walking", "Cycling"]
    )

    mode_dict = {
        "Driving": "driving-car",
        "Walking": "foot-walking",
        "Cycling": "cycling-regular"
    }

    if origin:
        google_transit_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={origin}"
            f"&destination={destination_lat},{destination_lon}"
            "&travelmode=transit"
        )

        st.link_button("Open public transport directions", google_transit_url)

    if st.button("Show Route"):
        if origin:
            try:
                geocode = ors_client.pelias_search(
                    text=origin,
                    country="FR",
                    size=1
                )

                origin_coords = geocode["features"][0]["geometry"]["coordinates"]

                destination_coords = [
                    destination_lon,
                    destination_lat
                ]

                route = ors_client.directions(
                    coordinates=[origin_coords, destination_coords],
                    profile=mode_dict[travel_mode],
                    format="geojson"
                )

                route_coords = route["features"][0]["geometry"]["coordinates"]
                route_line = [[coord[1], coord[0]] for coord in route_coords]

                distance_km = route["features"][0]["properties"]["segments"][0]["distance"] / 1000
                duration_min = route["features"][0]["properties"]["segments"][0]["duration"] / 60

                st.success(
                    f"Route found: {distance_km:.2f} km, about {duration_min:.0f} minutes"
                )

                route_map = folium.Map(
                    location=[destination_lat, destination_lon],
                    zoom_start=13,
                    tiles="CartoDB dark_matter"
                )

                folium.Marker(
                    location=[origin_coords[1], origin_coords[0]],
                    popup="Origin",
                    icon=folium.Icon(color="green", icon="play")
                ).add_to(route_map)

                folium.Marker(
                    location=[destination_lat, destination_lon],
                    popup=destination_row["name"],
                    icon=folium.Icon(color="red", icon="flag")
                ).add_to(route_map)

                folium.PolyLine(
                    route_line,
                    weight=5,
                    opacity=0.8
                ).add_to(route_map)

                st_folium(route_map, width=1100, height=550)

            except Exception as e:
                st.error("Could not calculate route. Try a more specific starting address.")
                st.write(e)
        else:
            st.warning("Please enter a starting point first.")

else:
    st.warning("No destinations available for this selection.")