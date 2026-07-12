import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import openrouteservice
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import math
from utils.theme import apply_theme, style_folium_map

apply_theme()

st.set_page_config(page_title="TourInsight | Trip Itinerary Builder", layout="wide")

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
ORS_API_KEY = os.getenv("ORS_API_KEY")


@st.cache_resource
def get_engine():
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


@st.cache_resource
def get_ors_client():
    return openrouteservice.Client(key=ORS_API_KEY)


@st.cache_data(ttl=3600)
def load_poi(_engine):
    with _engine.connect() as conn:
        return pd.read_sql("SELECT * FROM dim_poi", conn)


engine = get_engine()
ors_client = get_ors_client()
df = load_poi(engine)

ACCOMMODATION_CATEGORIES = {"hotel", "hostel", "guest_house"}

DAY_COLORS = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue", "pink"]
ORS_MODE = {"Walking": "foot-walking", "Driving": "driving-car"}
SPEED_KMH = {"Walking": 4.5, "Driving": 30}  # rough estimates for planning purposes only

st.header("🗺️ Trip Itinerary Builder")
st.write(
    "Pick a city, your interests, and how many days you have — this builds a "
    "day-by-day route through nearby points of interest so you're not "
    "zig-zagging across town."
)

st.divider()


# --- Helpers ---
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def nearest_neighbor_order(points):
    """points: list of dicts with 'lat','lon'. Returns list reordered to
    minimize backtracking, using a simple greedy nearest-neighbor heuristic."""
    if len(points) <= 2:
        return points
    remaining = points[:]
    route = [remaining.pop(0)]
    while remaining:
        last = route[-1]
        nearest_idx = min(
            range(len(remaining)),
            key=lambda i: haversine_km(last["lat"], last["lon"], remaining[i]["lat"], remaining[i]["lon"])
        )
        route.append(remaining.pop(nearest_idx))
    return route


def split_into_days(ordered_points, n_days):
    """Splits an ordered route into n_days contiguous, roughly equal chunks."""
    n = len(ordered_points)
    base, remainder = divmod(n, n_days)
    days, idx = [], 0
    for d in range(n_days):
        size = base + (1 if d < remainder else 0)
        days.append(ordered_points[idx: idx + size])
        idx += size
    return [day for day in days if day]  # drop empty days if fewer stops than days


def stratified_sample(frame, n, seed=42):
    """Samples n rows spread across categories rather than dominated by the
    most common category, so an itinerary isn't all restaurants."""
    if len(frame) <= n:
        return frame
    groups = [g.sample(frac=1, random_state=seed).reset_index(drop=True) for _, g in frame.groupby("category")]
    picked, i = [], 0
    while len(picked) < n:
        progressed = False
        for g in groups:
            if i < len(g):
                picked.append(g.iloc[i])
                progressed = True
                if len(picked) == n:
                    break
        if not progressed:
            break
        i += 1
    return pd.DataFrame(picked)


# --- Controls ---
cities = sorted(df["city"].dropna().unique())
categories = sorted(c for c in df["category"].dropna().unique() if c not in ACCOMMODATION_CATEGORIES)

c1, c2 = st.columns([1, 2])
with c1:
    selected_city = st.selectbox("City", cities)
with c2:
    selected_categories = st.multiselect("Interests", categories, default=categories)

c3, c4, c5 = st.columns(3)
with c3:
    n_days = st.slider("Number of days", 1, 5, 2)
with c4:
    stops_per_day = st.slider("Target stops per day", 2, 8, 4)
with c5:
    travel_mode = st.selectbox("Travel mode (for time estimates)", ["Walking", "Driving"])

city_df = df[
    (df["city"] == selected_city)
    & (df["category"].isin(selected_categories))
].dropna(subset=["lat", "lon"])

if city_df.empty:
    st.warning("No points of interest match this city/interest combination. Try widening your interests.")
    st.stop()

total_needed = n_days * stops_per_day
sampled_df = stratified_sample(city_df, total_needed)

st.caption(
    f"Using {len(sampled_df)} of {len(city_df)} matching points of interest in {selected_city} "
    f"(spread across categories to keep the trip varied)."
)

st.divider()

# --- Build the route order and split by day ---
points = sampled_df.to_dict("records")
ordered = nearest_neighbor_order(points)
day_groups = split_into_days(ordered, n_days)

# --- Overview map ---
st.subheader("Itinerary Overview")

center_lat = sampled_df["lat"].mean()
center_lon = sampled_df["lon"].mean()
m = folium.Map(location=[center_lat, center_lon], zoom_start=13, tiles="CartoDB dark_matter")
style_folium_map(m)

for day_idx, stops in enumerate(day_groups):
    color = DAY_COLORS[day_idx % len(DAY_COLORS)]
    coords = []
    for stop_idx, stop in enumerate(stops, start=1):
        coords.append([stop["lat"], stop["lon"]])
        folium.Marker(
            location=[stop["lat"], stop["lon"]],
            tooltip=f"Day {day_idx + 1}, Stop {stop_idx}: {stop['name']}",
            popup=folium.Popup(f"<b>Day {day_idx + 1} · Stop {stop_idx}</b><br>{stop['name']}<br>{stop['category']}", max_width=250),
            icon=folium.DivIcon(html=f"""
                <div style="background-color:{color}; color:white; border-radius:50%;
                width:24px; height:24px; display:flex; align-items:center; justify-content:center;
                font-size:12px; font-weight:bold; border:2px solid white;">{stop_idx}</div>
            """)
        ).add_to(m)
    if len(coords) > 1:
        folium.PolyLine(coords, color=color, weight=3, opacity=0.7, dash_array="6").add_to(m)

st_folium(m, width=1100, height=550, key="itinerary_overview_map")
st.caption(
    "Numbered pins show visiting order within each day (color-coded by day). "
    "Dashed lines are straight-line connections, not real walking/driving routes — "
    "use the day detail section below to get an actual route for a specific day."
)

st.divider()

# --- Day-by-day breakdown ---
st.subheader("Day-by-Day Plan")

speed = SPEED_KMH[travel_mode]
for day_idx, stops in enumerate(day_groups):
    total_km = sum(
        haversine_km(stops[i]["lat"], stops[i]["lon"], stops[i + 1]["lat"], stops[i + 1]["lon"])
        for i in range(len(stops) - 1)
    )
    est_minutes = (total_km / speed) * 60

    with st.expander(f"Day {day_idx + 1} — {len(stops)} stops · ~{total_km:.1f} km · ~{est_minutes:.0f} min {travel_mode.lower()} time", expanded=(day_idx == 0)):
        for stop_idx, stop in enumerate(stops, start=1):
            address = stop.get("address") if pd.notna(stop.get("address")) and stop.get("address") != "" else "Address not available"
            st.markdown(f"**{stop_idx}. {stop['name']}** — _{stop['category']}_  \n{address}")

st.divider()

# --- Real route for a selected day ---
st.subheader("Get a Real Route for One Day")

day_options = [f"Day {i + 1}" for i in range(len(day_groups))]
focus_day_label = st.selectbox("Choose a day to route", day_options)
focus_day_idx = day_options.index(focus_day_label)
focus_stops = day_groups[focus_day_idx]

route_key = (selected_city, focus_day_label, travel_mode, tuple(s["name"] for s in focus_stops))
if st.session_state.get("itinerary_route_key") != route_key:
    st.session_state.pop("itinerary_route_result", None)
    st.session_state["itinerary_route_key"] = route_key

if len(focus_stops) < 2:
    st.info("This day only has one stop — nothing to route between.")
else:
    if st.button(f"Calculate real {travel_mode.lower()} route for {focus_day_label}"):
        try:
            coordinates = [[s["lon"], s["lat"]] for s in focus_stops]
            route = ors_client.directions(
                coordinates=coordinates,
                profile=ORS_MODE[travel_mode],
                format="geojson"
            )
            route_coords = route["features"][0]["geometry"]["coordinates"]
            route_line = [[c[1], c[0]] for c in route_coords]
            distance_km = route["features"][0]["properties"]["segments"]
            total_distance = sum(seg["distance"] for seg in distance_km) / 1000
            total_duration = sum(seg["duration"] for seg in distance_km) / 60

            st.session_state["itinerary_route_result"] = {
                "route_line": route_line,
                "distance_km": total_distance,
                "duration_min": total_duration,
                "stops": focus_stops,
            }
        except Exception as e:
            st.session_state.pop("itinerary_route_result", None)
            st.error("Could not calculate a real route for this day's stops.")
            with st.expander("Debug details"):
                st.write(e)

    result = st.session_state.get("itinerary_route_result")
    if result:
        st.success(f"{focus_day_label}: {result['distance_km']:.2f} km, about {result['duration_min']:.0f} minutes ({travel_mode.lower()})")

        route_map = folium.Map(
            location=[result["stops"][0]["lat"], result["stops"][0]["lon"]],
            zoom_start=14,
            tiles="CartoDB dark_matter"
        )
        style_folium_map(route_map)
        for stop_idx, stop in enumerate(result["stops"], start=1):
            folium.Marker(
                location=[stop["lat"], stop["lon"]],
                tooltip=f"Stop {stop_idx}: {stop['name']}",
                icon=folium.Icon(color="green" if stop_idx == 1 else ("red" if stop_idx == len(result["stops"]) else "blue"),
                                  icon="play" if stop_idx == 1 else ("flag" if stop_idx == len(result["stops"]) else "map-marker"),
                                  prefix="fa")
            ).add_to(route_map)
        folium.PolyLine(result["route_line"], weight=5, opacity=0.85).add_to(route_map)
        st_folium(route_map, width=1100, height=550, key="itinerary_route_map")

st.divider()

# ---------- SIMPLE FOOTER ----------
st.caption("TourInsight | France tourism and weather analytics project")