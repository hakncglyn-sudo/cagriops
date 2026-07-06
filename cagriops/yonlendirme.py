"""Çağrı yönlendirme kural motoru.

Bir çağrıyı en uygun temsilciye atamak için beceri eşleşmesi, öncelik
ağırlığı, vardiya uygunluğu ve mevcut yükü birlikte puanlar.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from . import depo
from .modeller import Cagri, Temsilci

ONCELIK_AGIRLIK = {"dusuk": 1, "normal": 2, "yuksek": 4, "kritik": 8}

# Vardiya -> (başlangıç saati, bitiş saati). Gece vardiyası gün aşırıdır.
VARDIYA_SAATLERI = {
    "gunduz": (8, 16),
    "aksam": (16, 24),
    "gece": (0, 8),
}

# Beceri tam eşleşirse verilecek taban puan
BECERI_PUANI = 10
# "genel" becerisi her kategoriye kısmi uyum sağlar
GENEL_BECERI_PUANI = 4
# Temsilcinin üzerindeki her açık çağrı puanı bu kadar düşürür
YUK_CEZASI = 3
# Vardiyası uymayan temsilciye uygulanan ceza
VARDIYA_CEZASI = 6
# Kritik çağrılarda vardiya dışı temsilci de değerlendirilir (eskalasyon)
KRITIK_VARDIYA_ESNEK = True


def vardiyada_mi(temsilci: Temsilci, an: datetime) -> bool:
    baslangic, bitis = VARDIYA_SAATLERI[temsilci.vardiya]
    saat = an.hour
    if baslangic < bitis:
        return baslangic <= saat < bitis
    # gün aşırı vardiya (örn. gece: 0-8 zaten düz aralık ama genel çözüm dursun)
    return saat >= baslangic or saat < bitis


def beceri_puani(cagri: Cagri, temsilci: Temsilci) -> int:
    if cagri.kategori in temsilci.beceriler:
        return BECERI_PUANI
    if "genel" in temsilci.beceriler:
        return GENEL_BECERI_PUANI
    return 0


def temsilci_skoru(cagri: Cagri, temsilci: Temsilci,
                   acik_yuk: int, an: datetime) -> Optional[int]:
    """Temsilcinin bu çağrı için uygunluk puanı; hiç uygun değilse None."""
    if not temsilci.aktif:
        return None

    puan = beceri_puani(cagri, temsilci)
    if puan == 0:
        return None

    puan += ONCELIK_AGIRLIK.get(cagri.oncelik, 1)
    puan -= acik_yuk * YUK_CEZASI

    if not vardiyada_mi(temsilci, an):
        if cagri.oncelik == "kritik" and KRITIK_VARDIYA_ESNEK:
            puan -= VARDIYA_CEZASI
        else:
            return None

    return puan


def aday_listesi(cagri: Cagri, temsilciler: List[Temsilci],
                 an: datetime = None) -> List[Tuple[int, Temsilci]]:
    """(puan, temsilci) çiftlerini puana göre azalan sırada döndürür."""
    an = an or datetime.now()
    adaylar = []
    for temsilci in temsilciler:
        yuk = depo.temsilci_acik_yuku(temsilci.id)
        puan = temsilci_skoru(cagri, temsilci, yuk, an)
        if puan is not None:
            adaylar.append((puan, temsilci))
    adaylar.sort(key=lambda cift: (-cift[0], cift[1].id))
    return adaylar


def en_uygun_temsilci(cagri: Cagri, an: datetime = None) -> Optional[Temsilci]:
    adaylar = aday_listesi(cagri, depo.temsilci_listele(), an)
    if not adaylar:
        return None
    return adaylar[0][1]


def yonlendir(cagri_id: int, an: datetime = None) -> Tuple[Cagri, Temsilci]:
    """Çağrıyı en uygun temsilciye atar.

    Uygun temsilci yoksa LookupError fırlatır; çağrı 'acik' kalır.
    """
    cagri = depo.cagri_getir(cagri_id)
    if cagri is None:
        raise LookupError("Cagri bulunamadi: %s" % cagri_id)
    if cagri.durum != "acik":
        raise ValueError("Sadece acik cagrilar yonlendirilebilir")

    temsilci = en_uygun_temsilci(cagri, an)
    if temsilci is None:
        raise LookupError("Uygun temsilci bulunamadi (kategori=%s)" % cagri.kategori)

    guncel = depo.cagri_ata(cagri.id, temsilci.id)
    return guncel, temsilci
