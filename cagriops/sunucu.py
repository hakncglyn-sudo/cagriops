"""HTTP sunucusu: rota tablosu ve istek dağıtımı."""

import json
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qsl, urlparse

from . import api, ayarlar, kayitci

BASLANGIC_ZAMANI = time.time()

# (metot, desen, işleyici, id_alir_mi, govde_alir_mi)
ROTALAR = [
    ("GET", re.compile(r"^/cagrilar$"), api.cagrilar_listele, False, False),
    ("GET", re.compile(r"^/cagrilar/(\d+)$"), api.cagri_detay, True, False),
    ("POST", re.compile(r"^/cagrilar$"), api.cagri_olustur, False, True),
    ("POST", re.compile(r"^/cagrilar/(\d+)/kapat$"), api.cagri_kapat, True, False),
    ("POST", re.compile(r"^/cagrilar/(\d+)/yonlendir$"), api.cagri_yonlendir, True, False),
    ("GET", re.compile(r"^/temsilciler$"), api.temsilciler_listele, False, False),
    ("GET", re.compile(r"^/temsilciler/(\d+)$"), api.temsilci_detay, True, False),
    ("GET", re.compile(r"^/rapor/sla$"), lambda: api.sla_raporu(), False, False),
    ("GET", re.compile(r"^/rapor/bekleyenler$"), api.bekleyenler_raporu, False, False),
]


class CagriOpsIstekleri(BaseHTTPRequestHandler):
    server_version = "CagriOps/" + ayarlar.SURUM

    def do_GET(self):
        self._dagit("GET")

    def do_POST(self):
        self._dagit("POST")

    def _dagit(self, metot: str) -> None:
        parcali = urlparse(self.path)
        parametreler = dict(parse_qsl(parcali.query))

        for rota_metot, desen, isleyici, id_alir, govde_alir in ROTALAR:
            if rota_metot != metot:
                continue
            eslesme = desen.match(parcali.path)
            if not eslesme:
                continue

            try:
                if id_alir:
                    durum_kodu, govde = isleyici(int(eslesme.group(1)))
                elif govde_alir:
                    durum_kodu, govde = isleyici(self._govde_oku())
                elif isleyici.__code__.co_argcount == 0:
                    durum_kodu, govde = isleyici()
                else:
                    durum_kodu, govde = isleyici(parametreler)
            except Exception as hata:  # beklenmeyen hata: 500 döndür
                kayitci.hata_logla("unhandled exception on %s %s: %r"
                                   % (metot, parcali.path, hata))
                durum_kodu, govde = 500, {"hata": "Sunucu hatasi"}

            self._json_yanit(durum_kodu, govde)
            kayitci.istek_logla(metot, self.path, durum_kodu)
            return

        self._json_yanit(404, {"hata": "Boyle bir adres yok: %s" % parcali.path})

    def _govde_oku(self) -> dict:
        uzunluk = int(self.headers.get("Content-Length", 0))
        if uzunluk == 0:
            return {}
        ham = self.rfile.read(uzunluk)
        try:
            return json.loads(ham)
        except json.JSONDecodeError:
            return {}

    def _json_yanit(self, durum_kodu: int, govde: dict) -> None:
        veri = json.dumps(govde, ensure_ascii=False).encode("utf-8")
        self.send_response(durum_kodu)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(veri)))
        self.end_headers()
        self.wfile.write(veri)

    def log_message(self, bicim, *degiskenler):
        # Varsayılan stderr logunu kapat; kayitci zaten yazıyor.
        pass


def calistir(host: str = None, port: int = None) -> None:
    host = host or ayarlar.HOST
    port = port or ayarlar.PORT
    # Tek thread yeterli: sqlite bağlantısı tek bağlantı olarak paylaşılıyor.
    sunucu = HTTPServer((host, port), CagriOpsIstekleri)
    kayitci.kaydedici_al().info(
        "CagriOps %s basladi: http://%s:%s", ayarlar.SURUM, host, port
    )
    try:
        sunucu.serve_forever()
    except KeyboardInterrupt:
        kayitci.kaydedici_al().info("Sunucu durduruldu")
        sunucu.server_close()
