# Capstone A2 kabul testleri: /rapor/temsilci/{id} JSON sözleşmesi (bkz. katilimci/CAPSTONE-SPEC.md).

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from cagriops import api, depo, sunucu  # noqa: E402


def kurgu_veritabani_kur(test) -> None:
    """Geçici DB + kurgu veri (tests/test_depo.py deseninin capstone uyarlaması)."""
    depo.baglanti_kapat()
    test.gecici = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    test.gecici.close()
    conn = depo.baglanti_al(test.gecici.name)
    depo.sema_olustur(conn)
    conn.executemany(
        "INSERT INTO temsilciler (id, ad, beceriler, vardiya, aktif) "
        "VALUES (?, ?, ?, ?, 1)",
        [
            (1, "Deniz Acar", "ariza,genel", "gunduz"),
            (2, "Umut Sahin", "fatura", "aksam"),
            (3, "Lale Kaya", "genel", "gece"),
        ],
    )
    kayitlar = []

    def cagri(temsilci_id, cevap_sn, durum="kapandi"):
        kayitlar.append((
            "Ornek Musteri", "05001112233", "ornek@ornekmail.com", "genel",
            "normal", durum, "2026-07-01T09:00:00", cevap_sn,
            "2026-07-01T09:10:00" if durum == "kapandi" else None,
            temsilci_id, "",
        ))

    for _ in range(23):
        cagri(1, 10)
    for _ in range(2):
        cagri(1, 35)
    cagri(1, None, durum="atandi")  # cevaplanmamış çağrı: sayıya girer, ortalamaya girmez
    for deger in (15, 15, 30, 30):
        cagri(3, deger)

    conn.executemany(
        "INSERT INTO cagrilar (musteri_ad, musteri_telefon, musteri_eposta, "
        "kategori, oncelik, durum, acilis_zamani, cevap_suresi_sn, "
        "kapanis_zamani, temsilci_id, notlar) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        kayitlar,
    )
    conn.commit()


def kurgu_veritabani_kapat(test) -> None:
    depo.baglanti_kapat()
    os.unlink(test.gecici.name)


class TemsilciRaporuTestleri(unittest.TestCase):
    def setUp(self):
        kurgu_veritabani_kur(self)

    def tearDown(self):
        kurgu_veritabani_kapat(self)

    def test_rota_kayitli(self):
        eslesenler = [
            rota for rota in sunucu.ROTALAR
            if rota[0] == "GET" and rota[1].match("/rapor/temsilci/7")
        ]
        self.assertTrue(
            eslesenler,
            "sunucu.ROTALAR icinde GET /rapor/temsilci/{id} rotasi bulunamadi",
        )

    def test_normal_temsilci_raporu(self):
        durum, govde = api.temsilci_raporu(1)
        self.assertEqual(durum, 200)
        rapor = govde["rapor"]
        self.assertEqual(rapor["temsilci_id"], 1)
        self.assertEqual(rapor["ad"], "Deniz Acar")
        self.assertEqual(rapor["cagri_sayisi"], 26)
        self.assertEqual(rapor["ortalama_cevap_sn"], 12.0)
        self.assertEqual(rapor["sla_uyum_yuzde"], 92.0)

    def test_cagrisiz_temsilci(self):
        durum, govde = api.temsilci_raporu(2)
        self.assertEqual(durum, 200)
        rapor = govde["rapor"]
        self.assertEqual(rapor["cagri_sayisi"], 0)
        self.assertIsNone(rapor["ortalama_cevap_sn"])
        self.assertIsNone(rapor["sla_uyum_yuzde"])

    def test_olmayan_temsilci(self):
        durum, govde = api.temsilci_raporu(77)
        self.assertEqual(durum, 404)
        self.assertEqual(govde, {"hata": "Temsilci bulunamadi"})


if __name__ == "__main__":
    unittest.main()
