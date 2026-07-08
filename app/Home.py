import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

st.set_page_config(
    page_title="TourInsight",
    page_icon="🇫🇷",
    layout="wide"
)

#Get data from Neon
DATABASE_URL = os.getenv("DATABASE_URL")
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