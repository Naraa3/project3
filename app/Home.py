import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

st.set_page_config(
    page_title="TourInsight",
    page_icon="🇫🇷",
    layout="wide"
)

DATABASE_URL = "postgresql://neondb_owner:npg_MBG4insD6VQe@ep-old-recipe-atuuayxa-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

engine = create_engine(DATABASE_URL)

st.title("🇫🇷 TourInsight")
st.subheader("Interactive Tourism Analytics for Major French Cities")

@st.cache_data
def load_data():
    query = "SELECT * FROM dim_poi"
    return pd.read_sql(query, engine)

df = load_data()

st.write("Data preview:")
st.dataframe(df.head())

st.write("Total rows:", len(df))