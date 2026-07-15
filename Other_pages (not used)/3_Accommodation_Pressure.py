import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
from utils.theme import apply_theme

apply_theme()

st.set_page_config(
    page_title="TourInsight | Accommodation Pressure",
    layout="wide"
)

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


@st.cache_resource
def get_engine():
    return create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


@st.cache_data(ttl=3600)
def load_data(_engine):
    with _engine.connect() as conn:
        return pd.read_sql("SELECT * FROM dim_poi", conn)


engine = get_engine()
df = load_data(engine)

# --- Define supply (lodging) vs demand (everything that draws a visitor) ---
ACCOMMODATION_CATEGORIES = {"hotel", "hostel", "guest_house"}

df = df.dropna(subset=["city", "category"])
df["bucket"] = df["category"].apply(
    lambda c: "accommodation" if c in ACCOMMODATION_CATEGORIES else "attraction"
)

st.header("Accommodation Pressure")
st.write(
    "How many things there are to see and do in a city, relative to how many "
    "places there are to stay. A high pressure ratio means a city has lots to "
    "offer visitors but relatively few listed lodging options — a potential "
    "sign of an under-served or up-and-coming destination. A low ratio means "
    "lodging supply is generous relative to attractions."
)

st.divider()

# --- Build per-city summary ---
pivot = (
    df.groupby(["city", "bucket"]).size().unstack(fill_value=0)
)
for col in ["accommodation", "attraction"]:
    if col not in pivot.columns:
        pivot[col] = 0

pivot["total_pois"] = pivot["accommodation"] + pivot["attraction"]

# Filter out cities with too little data to be meaningful
min_pois = st.slider(
    "Minimum total POIs for a city to be included",
    min_value=5, max_value=100, value=15, step=5,
    help="Cities with very few listed POIs produce unreliable ratios."
)
pivot = pivot[pivot["total_pois"] >= min_pois].copy()

# Cities with zero accommodation get an undefined ratio — flag them instead of
# dividing by zero, then treat them as maximum pressure for ranking purposes.
pivot["has_lodging"] = pivot["accommodation"] > 0
pivot["pressure_ratio"] = pivot.apply(
    lambda r: r["attraction"] / r["accommodation"] if r["accommodation"] > 0 else float("inf"),
    axis=1
)
pivot = pivot.reset_index()

if pivot.empty:
    st.warning("No cities meet the minimum POI threshold. Try lowering the slider.")
    st.stop()

finite = pivot[pivot["has_lodging"]]

# --- KPI row ---
col1, col2, col3, col4 = st.columns(4)

if not finite.empty:
    highest = finite.loc[finite["pressure_ratio"].idxmax()]
    lowest = finite.loc[finite["pressure_ratio"].idxmin()]
    col1.metric("🔥 Highest pressure", highest["city"], f"{highest['pressure_ratio']:.1f} attractions/lodging")
    col2.metric("😌 Lowest pressure", lowest["city"], f"{lowest['pressure_ratio']:.1f} attractions/lodging")
    col3.metric("📊 Median ratio", f"{finite['pressure_ratio'].median():.1f}")
else:
    col1.metric("🔥 Highest pressure", "N/A")
    col2.metric("😌 Lowest pressure", "N/A")
    col3.metric("📊 Median ratio", "N/A")

no_lodging_count = (~pivot["has_lodging"]).sum()
col4.metric("🚫 Cities with no listed lodging", no_lodging_count)

st.divider()

# --- Quadrant bubble chart ---
st.subheader("Supply vs. Demand by City")

if not finite.empty:
    med_supply = finite["accommodation"].median()
    med_demand = finite["attraction"].median()

    fig_bubble = px.scatter(
        finite, x="accommodation", y="attraction",
        size="total_pois", color="pressure_ratio",
        color_continuous_scale="OrRd",
        hover_name="city",
        labels={
            "accommodation": "Lodging POIs (supply)",
            "attraction": "Attraction POIs (demand)",
            "pressure_ratio": "Pressure ratio"
        },
        title="Each bubble is a city — size = total POIs, color = pressure ratio"
    )
    fig_bubble.add_vline(x=med_supply, line_dash="dash", line_color="gray", opacity=0.5)
    fig_bubble.add_hline(y=med_demand, line_dash="dash", line_color="gray", opacity=0.5)
    fig_bubble.update_traces(marker=dict(line=dict(width=1, color="white")))
    st.plotly_chart(fig_bubble, use_container_width=True)
    st.caption(
        "Upper-left of the dashed lines = high demand, low supply (potential opportunity zone). "
        "Lower-right = generous lodging relative to attractions."
    )
else:
    st.info("No cities with listed lodging to plot.")

st.divider()

# --- Leaderboard ---
st.subheader("Pressure Ratio Leaderboard")

leaderboard = finite.sort_values("pressure_ratio", ascending=False)
fig_leaderboard = px.bar(
    leaderboard, x="pressure_ratio", y="city", orientation="h",
    color="pressure_ratio", color_continuous_scale="OrRd",
    labels={"pressure_ratio": "Attractions per lodging POI", "city": "City"},
    title="Cities ranked by accommodation pressure"
)
fig_leaderboard.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
st.plotly_chart(fig_leaderboard, use_container_width=True)

if no_lodging_count > 0:
    with st.expander(f"⚠️ {no_lodging_count} city(ies) have no listed lodging at all"):
        st.dataframe(
            pivot[~pivot["has_lodging"]][["city", "attraction", "accommodation", "total_pois"]]
            .rename(columns={"attraction": "attractions", "accommodation": "lodging"}),
            hide_index=True, use_container_width=True
        )

st.divider()

# --- City drill-down ---
st.subheader("City Drill-Down")

selected_city = st.selectbox("Choose a city", sorted(pivot["city"].unique()))
city_df = df[df["city"] == selected_city]

dcol1, dcol2 = st.columns(2)

with dcol1:
    lodging_breakdown = (
        city_df[city_df["category"].isin(ACCOMMODATION_CATEGORIES)]["category"]
        .value_counts()
        .reset_index()
    )
    lodging_breakdown.columns = ["category", "count"]

    if not lodging_breakdown.empty:
        fig_lodging = px.bar(
            lodging_breakdown, x="category", y="count", color="category",
            title=f"{selected_city} — Lodging Breakdown"
        )
        st.plotly_chart(fig_lodging, use_container_width=True)
    else:
        st.warning(f"No listed lodging found for {selected_city}.")

with dcol2:
    top_attractions = (
        city_df[~city_df["category"].isin(ACCOMMODATION_CATEGORIES)]["category"]
        .value_counts()
        .head(8)
        .reset_index()
    )
    top_attractions.columns = ["category", "count"]

    if not top_attractions.empty:
        fig_attractions = px.bar(
            top_attractions, x="count", y="category", orientation="h",
            title=f"{selected_city} — Top Attraction Categories"
        )
        fig_attractions.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_attractions, use_container_width=True)
    else:
        st.warning(f"No attraction data found for {selected_city}.")

city_row = pivot[pivot["city"] == selected_city].iloc[0]
if city_row["has_lodging"]:
    st.info(
        f"**{selected_city}** has a pressure ratio of **{city_row['pressure_ratio']:.1f}** "
        f"({int(city_row['attraction'])} attractions vs {int(city_row['accommodation'])} lodging options)."
    )
else:
    st.warning(f"**{selected_city}** has no listed lodging options in the dataset.")

st.divider()

# ---------- SIMPLE FOOTER ----------
st.caption("TourInsight | France tourism and weather analytics project")