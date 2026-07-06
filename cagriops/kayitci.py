"""Loglama katmanı.

Tüm servis olayları hem konsola hem loglar/cagriops.log dosyasına yazılır.
"""

import logging
import os

from . import ayarlar

_kaydedici = None


def kaydedici_al() -> logging.Logger:
    global _kaydedici
    if _kaydedici is not None:
        return _kaydedici

    logger = logging.getLogger("cagriops")
    logger.setLevel(logging.INFO)

    bicim = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    os.makedirs(os.path.dirname(ayarlar.LOG_DOSYASI), exist_ok=True)
    dosya = logging.FileHandler(ayarlar.LOG_DOSYASI, encoding="utf-8")
    dosya.setFormatter(bicim)
    logger.addHandler(dosya)

    konsol = logging.StreamHandler()
    konsol.setFormatter(bicim)
    logger.addHandler(konsol)

    _kaydedici = logger
    return logger


def cagri_acildi_logla(cagri) -> None:
    kaydedici_al().info(
        "Yeni cagri acildi: id=%s musteri=%s telefon=%s eposta=%s kategori=%s",
        cagri.id, cagri.musteri_ad, cagri.musteri_telefon,
        cagri.musteri_eposta, cagri.kategori,
    )


def cagri_atandi_logla(cagri, temsilci) -> None:
    kaydedici_al().info(
        "Call %s assigned to agent %s (customer: %s, phone: %s)",
        cagri.id, temsilci.ad, cagri.musteri_ad, cagri.musteri_telefon,
    )


def cagri_kapandi_logla(cagri) -> None:
    kaydedici_al().info(
        "Call closed: id=%s customer=%s",
        cagri.id, cagri.musteri_ad,
    )


def istek_logla(metot: str, yol: str, durum_kodu: int) -> None:
    kaydedici_al().info("%s %s -> %s", metot, yol, durum_kodu)


def hata_logla(mesaj: str) -> None:
    kaydedici_al().error("ERROR: %s", mesaj)
