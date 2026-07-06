"""HTTP endpoint işleyicileri.

Her işleyici (durum_kodu, govde_sozlugu) döndürür; JSON'a çevirme sunucu
katmanındadır.
"""

from datetime import datetime

from . import depo, kayitci, raporlama, yonlendirme
from .modeller import Cagri, cagri_dogrula


def cagrilar_listele(parametreler: dict):
    durum = parametreler.get("durum")
    limit = int(parametreler.get("limit", 50))
    cagrilar = depo.cagri_listele(durum=durum, limit=limit)
    return 200, {"adet": len(cagrilar), "cagrilar": [c.sozluk() for c in cagrilar]}


def cagri_detay(cagri_id: int):
    cagri = depo.cagri_getir(cagri_id)
    if cagri is None:
        return 404, {"hata": "Cagri bulunamadi"}
    return 200, {"cagri": cagri.sozluk()}


def cagri_olustur(govde: dict):
    try:
        cagri_dogrula(
            govde.get("kategori", ""),
            govde.get("oncelik", "normal"),
            govde.get("musteri_telefon", ""),
        )
    except ValueError as hata:
        return 400, {"hata": str(hata)}

    cagri = Cagri(
        id=None,
        musteri_ad=govde.get("musteri_ad", ""),
        musteri_telefon=govde.get("musteri_telefon", ""),
        musteri_eposta=govde.get("musteri_eposta", ""),
        kategori=govde["kategori"],
        oncelik=govde.get("oncelik", "normal"),
        durum="acik",
        acilis_zamani=datetime.now().isoformat(timespec="seconds"),
        notlar=govde.get("notlar", ""),
    )
    cagri = depo.cagri_ekle(cagri)
    kayitci.cagri_acildi_logla(cagri)
    return 201, {"cagri": cagri.sozluk()}


def cagri_kapat(cagri_id: int):
    try:
        cagri = depo.cagri_durum_degistir(
            cagri_id, "kapandi",
            kapanis_zamani=datetime.now().isoformat(timespec="seconds"),
        )
    except LookupError:
        return 404, {"hata": "Cagri bulunamadi"}
    except ValueError as hata:
        return 409, {"hata": str(hata)}
    kayitci.cagri_kapandi_logla(cagri)
    return 200, {"cagri": cagri.sozluk()}


def cagri_yonlendir(cagri_id: int):
    try:
        cagri, temsilci = yonlendirme.yonlendir(cagri_id)
    except LookupError as hata:
        return 404, {"hata": str(hata)}
    except ValueError as hata:
        return 409, {"hata": str(hata)}
    kayitci.cagri_atandi_logla(cagri, temsilci)
    return 200, {"cagri": cagri.sozluk(), "temsilci": temsilci.sozluk()}


def temsilciler_listele(parametreler: dict):
    hepsi = parametreler.get("hepsi") == "1"
    temsilciler = depo.temsilci_listele(sadece_aktif=not hepsi)
    return 200, {"adet": len(temsilciler),
                 "temsilciler": [t.sozluk() for t in temsilciler]}


def temsilci_detay(temsilci_id: int):
    temsilci = depo.temsilci_getir(temsilci_id)
    if temsilci is None:
        return 404, {"hata": "Temsilci bulunamadi"}
    return 200, {
        "temsilci": temsilci.sozluk(),
        "acik_yuk": depo.temsilci_acik_yuku(temsilci_id),
    }


def sla_raporu():
    return 200, raporlama.sla_ozeti()


def bekleyenler_raporu(parametreler: dict):
    adet = int(parametreler.get("adet", 5))
    return 200, {"bekleyenler": raporlama.en_uzun_bekleyenler(adet)}
