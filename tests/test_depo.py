import os
import tempfile
import unittest
from datetime import datetime

from cagriops import depo
from cagriops.modeller import Cagri


def ornek_cagri(**degisiklikler) -> Cagri:
    alanlar = dict(
        id=None,
        musteri_ad="Deneme Musteri",
        musteri_telefon="05009998877",
        musteri_eposta="deneme@ornekmail.com",
        kategori="ariza",
        oncelik="normal",
        durum="acik",
        acilis_zamani=datetime(2026, 7, 1, 10, 0).isoformat(timespec="seconds"),
    )
    alanlar.update(degisiklikler)
    return Cagri(**alanlar)


class DepoTestleri(unittest.TestCase):
    def setUp(self):
        depo.baglanti_kapat()
        self.gecici = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.gecici.close()
        conn = depo.baglanti_al(self.gecici.name)
        depo.sema_olustur(conn)
        conn.execute(
            "INSERT INTO temsilciler (id, ad, beceriler, vardiya, aktif) "
            "VALUES (1, 'Test Temsilci', 'ariza,genel', 'gunduz', 1)"
        )
        conn.commit()

    def tearDown(self):
        depo.baglanti_kapat()
        os.unlink(self.gecici.name)

    def test_cagri_ekle_ve_getir(self):
        eklenen = depo.cagri_ekle(ornek_cagri())
        self.assertIsNotNone(eklenen.id)
        bulunan = depo.cagri_getir(eklenen.id)
        self.assertEqual(bulunan.musteri_ad, "Deneme Musteri")
        self.assertEqual(bulunan.durum, "acik")

    def test_olmayan_cagri_none_doner(self):
        self.assertIsNone(depo.cagri_getir(9999))

    def test_cagri_listele_durum_filtresi(self):
        depo.cagri_ekle(ornek_cagri())
        depo.cagri_ekle(ornek_cagri(durum="kapandi",
                                    kapanis_zamani="2026-07-01T10:12:00"))
        acik = depo.cagri_listele(durum="acik")
        self.assertEqual(len(acik), 1)
        self.assertEqual(acik[0].durum, "acik")

    def test_cagri_atama_durumu_gunceller(self):
        eklenen = depo.cagri_ekle(ornek_cagri())
        atanan = depo.cagri_ata(eklenen.id, 1)
        self.assertEqual(atanan.durum, "atandi")
        self.assertEqual(atanan.temsilci_id, 1)
        self.assertEqual(depo.temsilci_acik_yuku(1), 1)

    def test_kapali_cagri_atanamaz(self):
        eklenen = depo.cagri_ekle(
            ornek_cagri(durum="kapandi", kapanis_zamani="2026-07-01T10:12:00")
        )
        with self.assertRaises(ValueError):
            depo.cagri_ata(eklenen.id, 1)

    def test_cagri_kapatma(self):
        eklenen = depo.cagri_ekle(ornek_cagri())
        kapanan = depo.cagri_durum_degistir(
            eklenen.id, "kapandi", kapanis_zamani="2026-07-01T10:30:00"
        )
        self.assertEqual(kapanan.durum, "kapandi")
        self.assertEqual(kapanan.kapanis_zamani, "2026-07-01T10:30:00")


if __name__ == "__main__":
    unittest.main()
