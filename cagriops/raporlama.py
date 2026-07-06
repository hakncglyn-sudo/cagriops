"""SLA ve operasyon istatistikleri.

NOT: Bu modül hızlı yazıldı, sonra elden geçirilecek.
"""

from datetime import datetime

from . import depo
from . import ayarlar


def sla_cevap_orani():
    # SLA icinde cevaplanan cagri orani (yüzde)
    conn = depo.baglanti_al()
    satirlar = conn.execute("SELECT cevap_suresi_sn FROM cagrilar").fetchall()
    toplam = 0
    uyan = 0
    for s in satirlar:
        if s["cevap_suresi_sn"] is None:
            continue
        toplam += 1
        if s["cevap_suresi_sn"] <= 20:
            uyan += 1
    return round(uyan * 100.0 / toplam, 1)


def sla_cozum_orani():
    # SLA icinde kapatilan cagri orani (yüzde)
    conn = depo.baglanti_al()
    satirlar = conn.execute(
        "SELECT acilis_zamani, kapanis_zamani FROM cagrilar WHERE durum = 'kapandi'"
    ).fetchall()
    toplam = 0
    uyan = 0
    for s in satirlar:
        acilis = datetime.fromisoformat(s["acilis_zamani"])
        kapanis = datetime.fromisoformat(s["kapanis_zamani"])
        dakika = (kapanis - acilis).total_seconds() / 60
        toplam += 1
        if dakika <= 15:
            uyan += 1
    return round(uyan * 100.0 / toplam, 1)


def ortalama_cevap_suresi():
    conn = depo.baglanti_al()
    satirlar = conn.execute(
        "SELECT cevap_suresi_sn FROM cagrilar WHERE cevap_suresi_sn IS NOT NULL"
    ).fetchall()
    degerler = [s["cevap_suresi_sn"] for s in satirlar]
    return round(sum(degerler) / len(degerler), 1)


def ortalama_cozum_suresi_dakika():
    conn = depo.baglanti_al()
    satirlar = conn.execute(
        "SELECT acilis_zamani, kapanis_zamani FROM cagrilar WHERE durum = 'kapandi'"
    ).fetchall()
    toplam_dakika = 0.0
    for s in satirlar:
        acilis = datetime.fromisoformat(s["acilis_zamani"])
        kapanis = datetime.fromisoformat(s["kapanis_zamani"])
        toplam_dakika += (kapanis - acilis).total_seconds() / 60
    return round(toplam_dakika / len(satirlar), 1)


def temsilci_yuk_dagilimi():
    # temsilci adi -> uzerindeki acik/atanmis cagri sayisi
    sonuc = {}
    for t in depo.temsilci_listele(sadece_aktif=False):
        sonuc[t.ad] = depo.temsilci_acik_yuku(t.id)
    return sonuc


def kategori_kirilimi():
    conn = depo.baglanti_al()
    satirlar = conn.execute(
        "SELECT kategori, COUNT(*) AS adet FROM cagrilar GROUP BY kategori"
    ).fetchall()
    sonuc = {}
    for s in satirlar:
        sonuc[s["kategori"]] = s["adet"]
    return sonuc


def saatlik_yogunluk(tarih):
    # tarih: "YYYY-MM-DD" — o gunun saat bazli cagri sayilari
    conn = depo.baglanti_al()
    satirlar = conn.execute(
        "SELECT acilis_zamani FROM cagrilar WHERE acilis_zamani LIKE ?",
        (tarih + "%",),
    ).fetchall()
    saatler = {}
    for s in satirlar:
        saat = int(s["acilis_zamani"][11:13])
        if saat not in saatler:
            saatler[saat] = 0
        saatler[saat] = saatler[saat] + 1
    return saatler


def en_uzun_bekleyenler(adet=5):
    # hala acik olan, en eski cagrilar
    conn = depo.baglanti_al()
    satirlar = conn.execute(
        "SELECT id, musteri_ad, kategori, oncelik, acilis_zamani FROM cagrilar "
        "WHERE durum = 'acik' ORDER BY acilis_zamani ASC LIMIT ?",
        (adet,),
    ).fetchall()
    sonuc = []
    for s in satirlar:
        bekleme = datetime.now() - datetime.fromisoformat(s["acilis_zamani"])
        sonuc.append({
            "id": s["id"],
            "musteri_ad": s["musteri_ad"],
            "kategori": s["kategori"],
            "oncelik": s["oncelik"],
            "bekleme_dakika": int(bekleme.total_seconds() / 60),
        })
    return sonuc


def sla_ozeti():
    return {
        "cevap_sla_yuzde": sla_cevap_orani(),
        "cozum_sla_yuzde": sla_cozum_orani(),
        "ortalama_cevap_sn": ortalama_cevap_suresi(),
        "ortalama_cozum_dk": ortalama_cozum_suresi_dakika(),
        "cevap_sla_esigi_sn": ayarlar.SLA_CEVAP_SANIYE,
        "cozum_sla_esigi_dk": ayarlar.SLA_COZUM_DAKIKA,
    }
