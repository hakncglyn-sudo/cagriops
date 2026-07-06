"""Veri modelleri ve doğrulama kuralları."""

from dataclasses import dataclass, field
from typing import Optional

DURUMLAR = ("acik", "atandi", "beklemede", "kapandi")
ONCELIKLER = ("dusuk", "normal", "yuksek", "kritik")
KATEGORILER = ("fatura", "ariza", "iptal", "kampanya", "genel")
VARDIYALAR = ("gunduz", "aksam", "gece")

# Geçerli durum geçişleri: eski durum -> gidilebilecek durumlar
_DURUM_GECISLERI = {
    "acik": ("atandi", "kapandi"),
    "atandi": ("beklemede", "kapandi"),
    "beklemede": ("atandi", "kapandi"),
    "kapandi": (),
}


@dataclass
class Temsilci:
    id: int
    ad: str
    beceriler: list = field(default_factory=list)  # KATEGORILER alt kümesi
    vardiya: str = "gunduz"
    aktif: bool = True

    def sozluk(self) -> dict:
        return {
            "id": self.id,
            "ad": self.ad,
            "beceriler": list(self.beceriler),
            "vardiya": self.vardiya,
            "aktif": self.aktif,
        }


@dataclass
class Cagri:
    id: Optional[int]
    musteri_ad: str
    musteri_telefon: str
    musteri_eposta: str
    kategori: str
    oncelik: str = "normal"
    durum: str = "acik"
    acilis_zamani: str = ""          # ISO 8601
    cevap_suresi_sn: Optional[int] = None
    kapanis_zamani: Optional[str] = None
    temsilci_id: Optional[int] = None
    notlar: str = ""

    def sozluk(self) -> dict:
        return {
            "id": self.id,
            "musteri_ad": self.musteri_ad,
            "musteri_telefon": self.musteri_telefon,
            "musteri_eposta": self.musteri_eposta,
            "kategori": self.kategori,
            "oncelik": self.oncelik,
            "durum": self.durum,
            "acilis_zamani": self.acilis_zamani,
            "cevap_suresi_sn": self.cevap_suresi_sn,
            "kapanis_zamani": self.kapanis_zamani,
            "temsilci_id": self.temsilci_id,
            "notlar": self.notlar,
        }


def cagri_dogrula(kategori: str, oncelik: str, musteri_telefon: str) -> None:
    """Yeni çağrı alanlarını doğrular; geçersizse ValueError fırlatır."""
    if kategori not in KATEGORILER:
        raise ValueError("Gecersiz kategori: %s" % kategori)
    if oncelik not in ONCELIKLER:
        raise ValueError("Gecersiz oncelik: %s" % oncelik)
    rakamlar = musteri_telefon.replace(" ", "").lstrip("+")
    if not rakamlar.isdigit() or len(rakamlar) < 10:
        raise ValueError("Gecersiz telefon numarasi")


def durum_gecisi_gecerli_mi(eski: str, yeni: str) -> bool:
    """Bir çağrının eski durumdan yeni duruma geçebilir mi?"""
    return yeni in _DURUM_GECISLERI.get(eski, ())
