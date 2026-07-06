"""Sentetik veri üretici.

data/cagrilar.db dosyasını sıfırdan üretir (deterministik — her koşumda
aynı veri çıkar). Tüm isimler, telefonlar ve e-postalar uydurmadır.

Çalıştırma (repo kökünden):
    python araclar/seed_uret.py
"""

import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cagriops import ayarlar  # noqa: E402
from cagriops.depo import sema_olustur  # noqa: E402

ADLAR = [
    "Ayşe", "Mehmet", "Zeynep", "Mustafa", "Elif", "Ahmet", "Fatma", "Emre",
    "Merve", "Burak", "Seda", "Can", "Derya", "Okan", "Pınar", "Serkan",
    "Gamze", "Tolga", "Nazlı", "Uğur",
]
SOYADLAR = [
    "Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Arslan", "Doğan", "Kılıç",
    "Aydın", "Özdemir", "Koç", "Kurt", "Aksoy", "Polat", "Erdoğan", "Güneş",
]

TEMSILCILER = [
    (1, "Selin Aktaş", "fatura,genel", "gunduz", 1),
    (2, "Kerem Yıldız", "ariza", "gunduz", 1),
    (3, "Büşra Tan", "ariza,kampanya", "gunduz", 1),
    (4, "Onur Sezer", "iptal,fatura", "gunduz", 1),
    (5, "İrem Duran", "genel", "aksam", 1),
    (6, "Barış Ekinci", "ariza,genel", "aksam", 1),
    (7, "Ece Karan", "fatura,kampanya", "aksam", 1),
    (8, "Volkan Öz", "ariza", "gece", 1),
    (9, "Melis Ünal", "genel", "gece", 1),
    (10, "Hakan Sarp", "iptal", "gunduz", 0),  # işten ayrıldı, pasif
]

KATEGORI_AGIRLIK = [
    ("fatura", 30), ("ariza", 35), ("iptal", 10), ("kampanya", 15), ("genel", 10),
]
ONCELIK_AGIRLIK = [
    ("dusuk", 15), ("normal", 55), ("yuksek", 22), ("kritik", 8),
]

NOT_ORNEKLERI = [
    "",
    "",
    "Musteri daha once de aramis.",
    "Ust birime bilgi verildi.",
    "Geri arama sozu verildi.",
    "Kampanya kosullari okundu.",
    "Modem yeniden baslatildi, sorun suruyor.",
    "",
]

BASLANGIC_GUNU = datetime(2026, 6, 22, 8, 0, 0)
GUN_SAYISI = 14
CAGRI_SAYISI = 220


def agirlikli_sec(rng, cifler):
    degerler = [c[0] for c in cifler]
    agirliklar = [c[1] for c in cifler]
    return rng.choices(degerler, weights=agirliklar, k=1)[0]


def uret(db_yolu: str) -> None:
    rng = random.Random(42)

    os.makedirs(os.path.dirname(db_yolu), exist_ok=True)
    if os.path.exists(db_yolu):
        os.remove(db_yolu)

    conn = sqlite3.connect(db_yolu)
    sema_olustur(conn)

    conn.executemany(
        "INSERT INTO temsilciler (id, ad, beceriler, vardiya, aktif) VALUES (?,?,?,?,?)",
        TEMSILCILER,
    )

    kayitlar = []
    for _ in range(CAGRI_SAYISI):
        ad = "%s %s" % (rng.choice(ADLAR), rng.choice(SOYADLAR))
        telefon = "05%s" % "".join(str(rng.randint(0, 9)) for _ in range(9))
        eposta = "%s.%s@ornekmail.com" % (
            ad.split()[0].lower().replace("ş", "s").replace("ı", "i")
            .replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c"),
            rng.randint(1, 99),
        )
        kategori = agirlikli_sec(rng, KATEGORI_AGIRLIK)
        oncelik = agirlikli_sec(rng, ONCELIK_AGIRLIK)

        gun = rng.randint(0, GUN_SAYISI - 1)
        saat_kaymasi = rng.betavariate(2, 2) * 14  # 08:00-22:00 arası yoğunlaşır
        acilis = BASLANGIC_GUNU + timedelta(days=gun, hours=saat_kaymasi,
                                            minutes=rng.randint(0, 59))

        cevap_sn = max(3, int(rng.gauss(18, 12)))
        temsilci_id = None
        durum = "acik"
        kapanis = None

        zar = rng.random()
        if zar < 0.78:
            durum = "kapandi"
            temsilci_id = rng.randint(1, 9)
            cozum_dk = max(2, rng.gauss(12, 8))
            kapanis = (acilis + timedelta(minutes=cozum_dk)).isoformat(timespec="seconds")
        elif zar < 0.90:
            durum = "atandi"
            temsilci_id = rng.randint(1, 9)
        elif zar < 0.95:
            durum = "beklemede"
            temsilci_id = rng.randint(1, 9)
        # kalan %5 açık ve atanmamış

        kayitlar.append((
            ad, telefon, eposta, kategori, oncelik, durum,
            acilis.isoformat(timespec="seconds"), cevap_sn, kapanis,
            temsilci_id, rng.choice(NOT_ORNEKLERI),
        ))

    conn.executemany(
        """
        INSERT INTO cagrilar (musteri_ad, musteri_telefon, musteri_eposta,
                              kategori, oncelik, durum, acilis_zamani,
                              cevap_suresi_sn, kapanis_zamani, temsilci_id, notlar)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """,
        kayitlar,
    )
    conn.commit()

    adetler = conn.execute(
        "SELECT durum, COUNT(*) FROM cagrilar GROUP BY durum"
    ).fetchall()
    conn.close()

    print("Veritabani uretildi: %s" % db_yolu)
    print("Temsilci sayisi: %s" % len(TEMSILCILER))
    print("Cagri sayisi: %s" % CAGRI_SAYISI)
    for durum, adet in adetler:
        print("  %-10s %s" % (durum, adet))


if __name__ == "__main__":
    uret(ayarlar.DB_YOLU)
