import unittest

from cagriops.modeller import (
    Cagri,
    cagri_dogrula,
    durum_gecisi_gecerli_mi,
)


class CagriDogrulamaTestleri(unittest.TestCase):
    def test_gecerli_cagri_dogrulanir(self):
        cagri_dogrula("ariza", "yuksek", "05321234567")  # hata fırlatmamalı

    def test_gecersiz_kategori_reddedilir(self):
        with self.assertRaises(ValueError):
            cagri_dogrula("bilinmeyen", "normal", "05321234567")

    def test_gecersiz_oncelik_reddedilir(self):
        with self.assertRaises(ValueError):
            cagri_dogrula("fatura", "cok-acil", "05321234567")

    def test_kisa_telefon_reddedilir(self):
        with self.assertRaises(ValueError):
            cagri_dogrula("fatura", "normal", "12345")

    def test_bosluklu_telefon_kabul_edilir(self):
        cagri_dogrula("genel", "dusuk", "0532 123 45 67")


class DurumGecisiTestleri(unittest.TestCase):
    def test_acik_cagri_atanabilir(self):
        self.assertTrue(durum_gecisi_gecerli_mi("acik", "atandi"))

    def test_acik_cagri_dogrudan_kapanabilir(self):
        self.assertTrue(durum_gecisi_gecerli_mi("acik", "kapandi"))

    def test_kapali_cagri_tekrar_acilamaz(self):
        self.assertFalse(durum_gecisi_gecerli_mi("kapandi", "acik"))
        self.assertFalse(durum_gecisi_gecerli_mi("kapandi", "atandi"))

    def test_beklemedeki_cagri_atanabilir(self):
        self.assertTrue(durum_gecisi_gecerli_mi("beklemede", "atandi"))

    def test_acik_cagri_beklemeye_alinamaz(self):
        # önce atanması gerekir
        self.assertFalse(durum_gecisi_gecerli_mi("acik", "beklemede"))


class CagriSozlukTestleri(unittest.TestCase):
    def test_sozluk_tum_alanlari_icerir(self):
        cagri = Cagri(
            id=7, musteri_ad="Test Musteri", musteri_telefon="05001112233",
            musteri_eposta="test@ornekmail.com", kategori="fatura",
        )
        sozluk = cagri.sozluk()
        self.assertEqual(sozluk["id"], 7)
        self.assertEqual(sozluk["kategori"], "fatura")
        self.assertEqual(sozluk["durum"], "acik")
        self.assertIsNone(sozluk["temsilci_id"])


if __name__ == "__main__":
    unittest.main()
