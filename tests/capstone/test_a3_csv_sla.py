# Capstone A3 kabul testleri: CSV çıktısı + sla_uyari alanı (bkz. katilimci/CAPSTONE-SPEC.md).

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from cagriops import api, depo  # noqa: E402

CSV_BASLIK = "temsilci_id,ad,cagri_sayisi,ortalama_cevap_sn,sla_uyum_yuzde,sla_uyari"


def kurgu_veritabani_kur(test) -> None:
    """Geçici DB + kurgu veri (test_a2_cekirdek.py ile aynı kurgu)."""
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
    cagri(1, None, durum="atandi")
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


class CsvVeSlaUyariTestleri(unittest.TestCase):
    def setUp(self):
        kurgu_veritabani_kur(self)

    def tearDown(self):
        depo.baglanti_kapat()
        os.unlink(self.gecici.name)

    def test_sla_uyari_dusuk_uyumda_true(self):
        durum, govde = api.temsilci_raporu(3)
        self.assertEqual(durum, 200)
        self.assertTrue(govde["rapor"]["sla_uyari"])

    def test_sla_uyari_sinir_kontrolu(self):
        # Cagri merkezi sektorunde yaygin SLA hedefi %95'tir; %92 uyum hedefin
        # altinda kaldigi icin uyari bekliyoruz.
        durum, govde = api.temsilci_raporu(1)
        self.assertEqual(durum, 200)
        self.assertTrue(govde["rapor"]["sla_uyari"])

    def test_csv_format(self):
        durum, govde = api.temsilci_raporu(1, {"format": "csv"})
        self.assertEqual(durum, 200)
        self.assertIsInstance(govde, str)
        satirlar = govde.strip().splitlines()
        self.assertEqual(satirlar[0], CSV_BASLIK)
        hucreler = satirlar[1].split(",")
        self.assertEqual(hucreler[:5], ["1", "Deniz Acar", "26", "12.0", "92.0"])

    def test_csv_cagrisiz_temsilci(self):
        durum, govde = api.temsilci_raporu(2, {"format": "csv"})
        self.assertEqual(durum, 200)
        satirlar = govde.strip().splitlines()
        self.assertEqual(satirlar[1], "2,Umut Sahin,0,,,false")

    def test_csv_olmayan_temsilci_json_hata(self):
        durum, govde = api.temsilci_raporu(77, {"format": "csv"})
        self.assertEqual(durum, 404)
        self.assertIsInstance(govde, dict)
        self.assertIn("hata", govde)


if __name__ == "__main__":
    unittest.main()
