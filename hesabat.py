import os 
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine,URL,text

def engine_yarat():
    load_dotenv()
    if os.getenv("DB_PASSWORD") is None:
        raise SystemExit(".env tapilamdi ve ya icindie db_password yoxdur,pipline dayandi")
    unvan = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )
    engine =create_engine(unvan)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Postegrese qosuldu",os.getenv("DB_NAME"))
    return engine

