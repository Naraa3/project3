from sqlalchemy import create_engine
from sqlalchemy import text

engine = create_engine("postgresql://neondb_owner:npg_MBG4insD6VQe@ep-old-recipe-atuuayxa-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.fetchall())