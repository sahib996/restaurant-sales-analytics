import json
import requests
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine,URL,text

API_UNVANI = "http://127.0.0.1:8009"
LIMIT = 5
HEFTE_GUNLERI = {0: "Bazar ertəsi", 1: "Çərşənbə axşamı", 2: "Çərşənbə", 3: "Cümə axşamı",
                 4: "Cümə", 5: "Şənbə", 6: "Bazar"}
def api_al(yol,paramtrler):
    try:
        cavab = requests.get(API_UNVANI+ yol,params=paramtrler,timeout=5)
        cavab.raise_for_status()
        return cavab.json()
    except requests.exceptions.Timeout:
        print("xeta:server vaxdinda qosulmadi"+yol)
    except requests.exceptions.HTTPError:
        print("Xeta:",cavab.status_code,yol)
    except requests.exceptions.ConnectionError:
        print("Xeta:serevere qosulmaq olmadi,restoran.api isleyirmi?")
    return None
def xam_yaz(data,fayl_adi):
    with open(fayl_adi,"w",encoding="Utf-8") as f:
        json.dump(data, f, ensure_ascii=False,indent=2)
    print(fayl_adi,"yazildi")
def extract_kataloq(yol,acar):
    cavab= api_al(yol,{"limit":100})
    if cavab is None:
        raise SystemExit(acar +"alinmadi pieline dayandi")
    xam = cavab[acar]
    print(acar +" :",len(xam))
    xam_yaz(xam,acar +"_xam.json")
    return xam 
def extract_sifarisler():
    ilk = api_al("/sifarisler" ,{"limit": 1,"skip" : 0})
    if ilk is None:
        raise SystemExit("Sifarisler alinmadi pipeline dayandi")
    cemi = ilk ["cemi"]
    sifarisler_xam =[]
    for skip in range(0,cemi,LIMIT):
        sehife = api_al("/sifarisler" ,{"limit":LIMIT,"skip" :skip})
        if sehife is None:
            raise  SystemExit("Sifarisler bir sehifede alinmadi ,pipeline dayandi")
        print("skip =",skip,"->",len(sehife["sifarisler"]),"sifaris")
        for sifaris in sehife["sifarisler"]:
            sifarisler_xam.append(sifaris)
    print("Yiqilan sifaris",len(sifarisler_xam),"/" ,cemi)
    xam_yaz(sifarisler_xam,"sifarisler_xam.json")
    return sifarisler_xam
def transform_musteri(musteriler_xam):
    dim_musteri = pd.json_normalize(musteriler_xam)
    dim_musteri=dim_musteri[["musteri_id","ad","rayon"]]
    print("dim_musteri", list(dim_musteri.columns),len(dim_musteri),"setir")
    return dim_musteri
def transform_yemek(yemekler_xam):
    dim_yemek = pd.json_normalize(yemekler_xam)
    dim_yemek = dim_yemek.rename(columns={"kateqoriya.ad":"kateqoriya"})
    dim_yemek = dim_yemek[["yemek_id","ad","kateqoriya","qiymet"]]
    print("dim_yemek",list(dim_yemek.columns),len(dim_yemek) ,"setir")
    return dim_yemek
def trasnform_satis(sifarisler_xam,dim_yemek):
    satis = pd.json_normalize(sifarisler_xam,record_path="setirler",meta=["id","tarix","musteri_id","status"])
    print("Satis setirleri",len(satis))
    legv= satis["status"] == "ləğv edildi"
    print(satis[legv][["id","musteri_id","status"]])
    satis =satis[~legv]
    print("Leqvden sonra" ,len(satis))
    print(satis[satis.duplicated()][["id","sira","yemek_id"]])
    satis = satis.drop_duplicates()
    print("dublikatdan sonra",len(satis))
    satis = pd.merge(satis,dim_yemek[["yemek_id","qiymet"]],on="yemek_id" ,how="left")
    namelum = satis[satis["qiymet"].isna()]
    print(namelum[["id","sira","yemek_id"]])
    satis = satis.dropna(subset=["qiymet"])
    print("Namelum yemekden sonra",len(satis))
    satis["mebleg"] =satis["qiymet"] *satis["say"]
    satis["tarix"] =pd.to_datetime(satis["tarix"])
    satis = satis.rename(columns={"id":"sifaris_id"})
    fact_satis= satis[["sifaris_id", "sira", "tarix", "musteri_id", "yemek_id", "say", "mebleg"]]
    print("fact_satis:",list(fact_satis.columns),len(fact_satis) ,"setir")
    return fact_satis
def transform_tarix(fact_satis):
    gunler = pd.date_range(fact_satis["tarix"].min(),fact_satis["tarix"].max())
    dim_tarix =pd.DataFrame({
        "tarix":gunler,
        "il":gunler.year,
        "ay":gunler.month,
        "hefte_gunu":gunler.day_of_week.map(HEFTE_GUNLERI),
    })
    print(dim_tarix)
    return dim_tarix
def engine_yarat():
    load_dotenv()
    if os.getenv("DB_PASSWORD") is None:
        raise SystemExit(".env tapilmadi ve ya DB_PASSWORD yoxdu, pipeline dayandi")
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
        conn.execute(text("SELECT 1"))
    print("Postegrese qosuldu",os.getenv("DB_NAME"))
    return engine
def load(engine,dim_musteri,dim_yemek,dim_tarix,fact_satis):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_satis"))
        conn.execute(text("DELETE FROM dim_musteri"))
        conn.execute(text("DELETE FROM dim_yemek"))
        conn.execute(text("DELETE FROM dim_tarix"))
        dim_musteri.to_sql("dim_musteri",conn,if_exists ="append",index=False)
        dim_yemek.to_sql("dim_yemek",conn,if_exists ="append",index=False)
        dim_tarix.to_sql("dim_tarix",conn,if_exists ="append",index=False)
        fact_satis.to_sql("fact_satis",conn,if_exists ="append",index=False)
    with engine.connect() as conn:
        for cedvel in["dim_musteri","dim_yemek","dim_tarix","fact_satis"]:
            say = conn.execute(text("SELECT COUNT(*) FROM " + cedvel)).scalar()
            print("Postegresde " +cedvel+":",say,"setir")
def main():
    print("extract")
    yemekler_xam =extract_kataloq("/yemekler","yemekler")
    musteriler_xam = extract_kataloq("/musteriler","musteriler")
    sifarisler_xam = extract_sifarisler()
    print("transform")
    dim_musteri = transform_musteri(musteriler_xam)
    dim_yemek = transform_yemek(yemekler_xam)
    fact_satis = trasnform_satis(sifarisler_xam,dim_yemek)
    dim_tarix = transform_tarix(fact_satis)
    print("load")
    engine= engine_yarat()
    load(engine,dim_musteri,dim_yemek,dim_tarix,fact_satis)
    print("pipeline uqulra bitdi")
if __name__ == "__main__":
    main()



    

