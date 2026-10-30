# Restoranın məşq API-sı. Bu faylı olduğu kimi yapışdır, içini başa düşməyə ehtiyac yoxdur.
# İşə salmaq: python restoran_api.py      Dayandırmaq: Ctrl+C
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

YEMEKLER = [
    {"yemek_id": 1, "ad": "Mərci şorbası", "qiymet": 4.0, "kateqoriya": {"id": 1, "ad": "Şorba"}},
    {"yemek_id": 2, "ad": "Lülə kabab", "qiymet": 9.0, "kateqoriya": {"id": 2, "ad": "Kabab"}},
    {"yemek_id": 3, "ad": "Tikə kabab", "qiymet": 11.0, "kateqoriya": {"id": 2, "ad": "Kabab"}},
    {"yemek_id": 4, "ad": "Ayran", "qiymet": 1.5, "kateqoriya": {"id": 3, "ad": "İçki"}},
    {"yemek_id": 5, "ad": "Dovğa", "qiymet": 3.5, "kateqoriya": {"id": 1, "ad": "Şorba"}},
    {"yemek_id": 6, "ad": "Toyuq kababı", "qiymet": 8.0, "kateqoriya": {"id": 2, "ad": "Kabab"}},
    {"yemek_id": 7, "ad": "Çay dəsti", "qiymet": 5.0, "kateqoriya": {"id": 3, "ad": "İçki"}},
    {"yemek_id": 8, "ad": "Paxlava", "qiymet": 3.0, "kateqoriya": {"id": 4, "ad": "Şirniyyat"}},
]

MUSTERILER = [
    {"musteri_id": 1, "ad": "Leyla", "rayon": "Nəsimi"},
    {"musteri_id": 2, "ad": "Rauf", "rayon": "Yasamal"},
    {"musteri_id": 3, "ad": "Aynur", "rayon": "Nəsimi"},
    {"musteri_id": 4, "ad": "Tural", "rayon": "Xətai"},
    {"musteri_id": 5, "ad": "Səbinə", "rayon": "Yasamal"},
]


def sifaris(i, tarix, musteri_id, status, setirler):
    return {"id": i, "tarix": tarix, "musteri_id": musteri_id, "status": status,
            "setirler": [{"sira": s, "yemek_id": y, "say": n} for s, y, n in setirler]}


SIFARISLER = [
    sifaris(9001, "2026-11-02", 1, "çatdırıldı", [(1, 2, 2), (2, 4, 2)]),
    sifaris(9002, "2026-11-02", 2, "çatdırıldı", [(1, 1, 1)]),
    sifaris(9003, "2026-11-03", 3, "çatdırıldı", [(1, 3, 1), (2, 5, 1), (3, 7, 1)]),
    sifaris(9004, "2026-11-04", 4, "ləğv edildi", [(1, 6, 2), (2, 4, 2)]),
    sifaris(9005, "2026-11-05", 1, "çatdırıldı", [(1, 6, 1), (2, 8, 2)]),
    sifaris(9006, "2026-11-06", 5, "çatdırıldı", [(1, 2, 1), (2, 4, 1), (2, 4, 1)]),
    sifaris(9007, "2026-11-06", 2, "çatdırıldı", [(1, 3, 2), (2, 12, 1)]),
    sifaris(9008, "2026-11-07", 3, "çatdırıldı", [(1, 2, 3), (2, 4, 3), (3, 8, 3)]),
    sifaris(9009, "2026-11-07", 4, "çatdırıldı", [(1, 6, 2)]),
    sifaris(9010, "2026-11-08", 5, "çatdırıldı", [(1, 1, 2), (2, 5, 2)]),
    sifaris(9011, "2026-11-08", 1, "çatdırıldı", [(1, 3, 1), (2, 7, 1)]),
    sifaris(9012, "2026-11-08", 2, "çatdırıldı", [(1, 2, 2), (2, 8, 1), (3, 4, 2)]),
]


class Isleyici(BaseHTTPRequestHandler):
    def cavab_ver(self, kod, data):
        metn = json.dumps(data, ensure_ascii=False).encode("utf-8")
        try:
            self.send_response(kod)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(metn)))
            self.end_headers()
            self.wfile.write(metn)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass  # sorğu göndərən gözləməyib çıxıb, bu normaldır

    def sehife(self, siyahi, parametrler):
        limit = int(parametrler.get("limit", ["5"])[0])
        skip = int(parametrler.get("skip", ["0"])[0])
        return limit, skip, siyahi[skip:skip + limit]

    def do_GET(self):
        url = urlparse(self.path)
        parametrler = parse_qs(url.query)
        hisseler = [h for h in url.path.split("/") if h]
        siyahilar = {"yemekler": YEMEKLER, "musteriler": MUSTERILER, "sifarisler": SIFARISLER}
        try:
            if len(hisseler) == 1 and hisseler[0] in siyahilar:
                siyahi = siyahilar[hisseler[0]]
                limit, skip, hisse = self.sehife(siyahi, parametrler)
                self.cavab_ver(200, {"cemi": len(siyahi), "limit": limit, "skip": skip, hisseler[0]: hisse})
            else:
                self.cavab_ver(404, {"xeta": "Belə ünvan yoxdur"})
        except ValueError:
            self.cavab_ver(400, {"xeta": "limit və skip tam ədəd olmalıdır"})

    def log_request(self, code="-", size="-"):
        print(f"Sorğu gəldi: GET {self.path} -> {int(code)}", flush=True)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8009), Isleyici)
    print("Restoran API-sı işləyir: http://127.0.0.1:8009", flush=True)
    print("Dayandırmaq üçün Ctrl+C bas", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server dayandı")
        server.server_close()