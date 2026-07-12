import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import openrouteservice
from dotenv import load_dotenv
import os
from utils.theme import apply_theme, style_folium_map

apply_theme()

st.set_page_config(page_title="TourInsight | Explore France", layout="wide")

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
ORS_API_KEY = os.getenv("ORS_API_KEY")

# --- Connections cached as RESOURCES (persist across reruns), not data ---
@st.cache_resource
def get_engine():
    return create_engine(DATABASE_URL)

@st.cache_resource
def get_ors_client():
    return openrouteservice.Client(key=ORS_API_KEY)

engine = get_engine()
ors_client = get_ors_client()

# --- Data cached separately, with a TTL so it refreshes periodically ---
@st.cache_data(ttl=3600)
def load_poi():
    return pd.read_sql("SELECT * FROM dim_poi", engine)

@st.cache_data(ttl=3600)
def load_weather():
    return pd.read_sql("SELECT * FROM weather_current", engine)

df = load_poi()
weather_df = load_weather()

st.header("Explore France")
st.write("Find points of interest across major French cities")

# Sidebar filters
st.sidebar.header("Filters")
cities = sorted(df["city"].unique())
selected_city = st.sidebar.selectbox("Choose a city", cities)
city_weather = weather_df[weather_df["city"] == selected_city]

categories = sorted(df["category"].dropna().unique())
selected_categories = st.sidebar.multiselect("Choose categories", categories, default=categories)
search = st.sidebar.text_input("Search by name")

filtered_df = df[(df["city"] == selected_city) & (df["category"].isin(selected_categories))]
if search:
    filtered_df = filtered_df[filtered_df["name"].str.contains(search, case=False, na=False)]

# --- Metrics ---
col1 = st.columns(4)[0]

if not city_weather.empty:
    col1.metric("🌤 Temperature", f"{city_weather.iloc[0]['temperature_c']}°C")
else:
    col1.metric("🌤 Temperature", "N/A")

st.divider()

# --- Map ---
st.subheader(f"Map of {selected_city}")
map_df = filtered_df.dropna(subset=["lat", "lon"])

if len(map_df) > 1000:
    map_df = map_df.sample(1000, random_state=42)

# Style lookup for all categories
CATEGORY_STYLE = {
    "hotel": {"color": "blue", "icon": "hotel"},
    "restaurant": {"color": "red", "icon": "cutlery"},
    "cafe": {"color": "orange", "icon": "coffee"},
    "bar": {"color": "purple", "icon": "glass"},
    "museum": {"color": "darkblue", "icon": "university"},
    "gallery": {"color": "pink", "icon": "picture"},
    "attraction": {"color": "green", "icon": "star"},
    "viewpoint": {"color": "brown", "icon": "eye"},
    "monument": {"color": "darkred", "icon": "flag"},
    "memorial": {"color": "darkgray", "icon": "crosshairs"},
    "castle": {"color": "darkpurple", "icon": "home"},
    "park": {"color": "lightgreen", "icon": "tree"},
    "garden": {"color": "lightgreen", "icon": "leaf"},
    "beach": {"color": "lightblue", "icon": "umbrella"},
    "zoo": {"color": "cadetblue", "icon": "paw"},
    "theme_park": {"color": "violet", "icon": "play"},
    "ruins": {"color": "gray", "icon": "building"},
    "artwork": {"color": "gold", "icon": "art"},
    "church": {"color": "saddlebrown", "icon": "church"},
    "cathedral": {"color": "saddlebrown", "icon": "plus"},
    "hostel": {"color": "lightblue", "icon": "home"},
    "guest_house": {"color": "lightblue", "icon": "home"},
    "lavoir": {"color": "aqua", "icon": "tint"}
}
DEFAULT_STYLE = {"color": "gray", "icon": "info-sign"}

if len(map_df) > 0:
    m = folium.Map(
        location=[map_df["lat"].mean(), map_df["lon"].mean()],
        zoom_start=12,
        tiles="CartoDB dark_matter"
    )
    style_folium_map(m)
    marker_cluster = MarkerCluster().add_to(m)

    for _, row in map_df.iterrows():
        style = CATEGORY_STYLE.get(row["category"], DEFAULT_STYLE)
        address = row["address"] if pd.notna(row.get("address")) and row["address"] != "" else "Address not available"
        popup_html = f"<b>{row['name']}</b><br>Category: {row['category']}<br>Address: {address}<br>"

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row["name"],
            icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa")
        ).add_to(marker_cluster)

    st_folium(m, width=1100, height=550, key="explore_map")
else:
    st.warning("No map data available for this selection.")

st.divider()

# --- Directions ---
st.subheader("Get Directions")
destination_options = filtered_df.dropna(subset=["lat", "lon"]).copy()

if len(destination_options) > 0:
    destination_options["display_name"] = (
        destination_options["name"].fillna("Unknown") + " - "
        + destination_options["category"].fillna("") + " - "
        + destination_options["city"].fillna("")
    )

    origin = st.text_input("Enter your starting point", placeholder="Example: Lyon Part-Dieu, Paris Gare du Nord...")
    selected_destination = st.selectbox("Choose a destination", destination_options["display_name"])
    destination_row = destination_options[destination_options["display_name"] == selected_destination].iloc[0]
    destination_lat, destination_lon = destination_row["lat"], destination_row["lon"]

    travel_mode = st.selectbox("Travel mode", ["Driving", "Walking", "Cycling", "Public Transport"])

    # Clear any previously computed route if the destination or mode changed,
    # so we don't show a stale route for a new selection.
    route_key = (selected_destination, travel_mode)
    if st.session_state.get("route_key") != route_key:
        st.session_state.pop("route_result", None)
        st.session_state["route_key"] = route_key

    # Separate maps for each service — ORS has no transit profile, Google needs its own naming
    ORS_MODE = {"Driving": "driving-car", "Walking": "foot-walking", "Cycling": "cycling-regular"}
    GOOGLE_MODE = {"Driving": "driving", "Walking": "walking", "Cycling": "bicycling", "Public Transport": "transit"}

    if origin:
        google_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={origin}&destination={destination_lat},{destination_lon}"
            f"&travelmode={GOOGLE_MODE[travel_mode]}"
        )
        st.link_button(f"Open {travel_mode.lower()} directions in Google Maps", google_url)

    if travel_mode == "Public Transport":
        st.info("Turn-by-turn public transport routing isn't available here — use the Google Maps button above.")
    else:
        if st.button("Show Route"):
            if origin:
                try:
                    geocode = ors_client.pelias_search(text=origin, country="FR", size=1)

                    if not geocode["features"]:
                        st.error("Could not find that starting location. Try a more specific address.")
                    else:
                        origin_coords = geocode["features"][0]["geometry"]["coordinates"]
                        destination_coords = [destination_lon, destination_lat]

                        route = ors_client.directions(
                            coordinates=[origin_coords, destination_coords],
                            profile=ORS_MODE[travel_mode],
                            format="geojson"
                        )

                        route_coords = route["features"][0]["geometry"]["coordinates"]
                        route_line = [[c[1], c[0]] for c in route_coords]
                        distance_km = route["features"][0]["properties"]["segments"][0]["distance"] / 1000
                        duration_min = route["features"][0]["properties"]["segments"][0]["duration"] / 60

                        # Save results to session_state so they persist across reruns
                        # (e.g. panning/zooming the map below triggers a rerun).
                        st.session_state["route_result"] = {
                            "origin_coords": origin_coords,
                            "destination_lat": destination_lat,
                            "destination_lon": destination_lon,
                            "destination_name": destination_row["name"],
                            "route_line": route_line,
                            "distance_km": distance_km,
                            "duration_min": duration_min,
                        }

                except Exception as e:
                    st.session_state.pop("route_result", None)
                    st.error("Could not calculate route. Try a more specific starting address.")
                    with st.expander("Debug details"):
                        st.write(e)
            else:
                st.warning("Please enter a starting point first.")

        # Render the stored route (if any) on every rerun, not just the run
        # where "Show Route" was clicked.
        result = st.session_state.get("route_result")
        if result:
            st.success(f"Route found: {result['distance_km']:.2f} km, about {result['duration_min']:.0f} minutes")

            route_map = folium.Map(
                location=[result["destination_lat"], result["destination_lon"]],
                zoom_start=13,
                tiles="CartoDB dark_matter"
            )
            style_folium_map(route_map)
            folium.Marker(
                location=[result["origin_coords"][1], result["origin_coords"][0]],
                popup="Origin",
                icon=folium.Icon(color="green", icon="play")
            ).add_to(route_map)
            folium.Marker(
                location=[result["destination_lat"], result["destination_lon"]],
                popup=result["destination_name"],
                icon=folium.Icon(color="red", icon="flag")
            ).add_to(route_map)
            folium.PolyLine(result["route_line"], weight=5, opacity=0.8).add_to(route_map)
            st_folium(route_map, width=1100, height=550, key="route_map")
else:
    st.warning("No destinations available for this selection.")


st.divider()

# ---------- SIMPLE FOOTER ----------
st.caption("TourInsight | France tourism and weather analytics project")