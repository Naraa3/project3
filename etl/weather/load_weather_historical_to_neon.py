import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

df = pd.read_csv("data/clean/weather/weather_historical_monthly.csv")
df.to_sql(name="weather_historical_monthly", con=engine, if_exists="replace", index=False)
print("Historical weather loaded to Neon.")