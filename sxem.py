import os 
from dotenv import load_dotenv
from sqlalchemy import create_engine,URL,text
from sqlalchemy.exc import IntegrityError

def engine_yarat():
    load_dotenv()
    if os.getenv("DB_PASSWORD") is None:
        raise SystemExit(".env tapilamdi ve ya icinde db_password yoxdur, pipeline dayandi")
    unvan = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )
    engine = create_engine(unvan)
    with engine.connect() as conn:
        conn.execute(text("Select 1"))
    print("Postegrese qosuldu", os.getenv("DB_NAME"))
    return engine
def sxem_qur(engine):
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS fact_satis"))
        conn.execute(text("DROP TABLE IF EXISTS dim_musteri"))
        conn.execute(text("DROP TABLE IF EXISTS dim_yemek"))
        conn.execute(text("DROP TABLE IF EXISTS dim_tarix"))
        conn.execute(text("""
            CREATE TABLE dim_musteri(
                  musteri_id INTEGER PRIMARY KEY,
                  ad TEXT,
                  rayon TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE dim_yemek(
            yemek_id INTEGER PRIMARY KEY,   
            ad  TEXT,
            kateqoriya text,
            qiymet NUMERIC(8,2)
            )
        """))
        conn.execute(text("""
            CREATE TABLE dim_tarix(
            tarix DATE PRIMARY KEY,
            il INTEGER,
            ay INTEGER,
            hefte_gunu TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE fact_satis(
            sifaris_id INTEGER,
            sira INTEGER,
            tarix DATE REFERENCES dim_tarix (tarix),
            musteri_id INTEGER REFERENCES dim_musteri (musteri_id),
            yemek_id INTEGER REFERENCES dim_yemek (yemek_id),
            say INTEGER,
            mebleg NUMERIC(8,2), 
            PRIMARY KEY (sifaris_id,sira)
            )
        """))
    print("sxem quruldu: dim_musteri, dim_yemek, dim_tarix, fact_satis")
def main():
    engine = engine_yarat()
    sxem_qur(engine)
if __name__ == "__main__":
    main()



