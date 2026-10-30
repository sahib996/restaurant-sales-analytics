# Restoran satışlarının analitikası: star schema və ETL pipeline

Restoranın sifariş məlumatlarını REST API-dən çıxaran, pandas ilə təmizləyən, PostgreSQL-də star schema-ya yükləyən və SQL ilə satış hesabatları hazırlayan layihə.

**Texnologiyalar:** Python · pandas · PostgreSQL · SQLAlchemy · requests

## Məlumat modeli (star schema)

| Cədvəl | Növü | Açarlar |
|---|---|---|
| `dim_musteri` | dimension | PRIMARY KEY: musteri_id |
| `dim_yemek` | dimension | PRIMARY KEY: yemek_id |
| `dim_tarix` | dimension | PRIMARY KEY: tarix |
| `fact_satis` | fact | PRIMARY KEY: (sifaris_id, sira); FOREIGN KEY: tarix, musteri_id, yemek_id |

**Grain:** `fact_satis` cədvəlində bir sətir sifarişdəki bir yeməkdir.

## Pipeline

1. **Extract:** `/yemekler`, `/musteriler` və `/sifarisler` səhifələmə (limit / skip) ilə çıxarılır, xam JSON fayllara yazılır.
2. **Transform:** ləğv edilmiş sifarişlər, təkrarlanan sətirlər və kataloqda olmayan yeməklər təmizlənir; məbləğ hesablanır; `dim_tarix` satış dövrünün bütün günləri ilə qurulur.
3. **Load:** bütün
