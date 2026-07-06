"""SQLite erişim katmanı."""

import sqlite3
from typing import List, Optional

from . import ayarlar
from .modeller import Cagri, Temsilci, durum_gecisi_gecerli_mi

_baglanti = None


def baglanti_al(db_yolu: str = None) -> sqlite3.Connection:
    """Süreç boyunca tek bağlantı kullanılır."""
    global _baglanti
    if _baglanti is None:
        _baglanti = sqlite3.connect(db_yolu or ayarlar.DB_YOLU)
        _baglanti.row_factory = sqlite3.Row
    return _baglanti


def baglanti_kapat() -> None:
    global _baglanti
    if _baglanti is not None:
        _baglanti.close()
        _baglanti = None


def sema_olustur(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS temsilciler (
            id INTEGER PRIMARY KEY,
            ad TEXT NOT NULL,
            beceriler TEXT NOT NULL,
            vardiya TEXT NOT NULL,
            aktif INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS cagrilar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_ad TEXT NOT NULL,
            musteri_telefon TEXT NOT NULL,
            musteri_eposta TEXT NOT NULL,
            kategori TEXT NOT NULL,
            oncelik TEXT NOT NULL,
            durum TEXT NOT NULL,
            acilis_zamani TEXT NOT NULL,
            cevap_suresi_sn INTEGER,
            kapanis_zamani TEXT,
            temsilci_id INTEGER,
            notlar TEXT DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS ix_cagrilar_durum ON cagrilar(durum);
        CREATE INDEX IF NOT EXISTS ix_cagrilar_acilis ON cagrilar(acilis_zamani);
        """
    )
    conn.commit()


def _satirdan_cagri(satir: sqlite3.Row) -> Cagri:
    return Cagri(
        id=satir["id"],
        musteri_ad=satir["musteri_ad"],
        musteri_telefon=satir["musteri_telefon"],
        musteri_eposta=satir["musteri_eposta"],
        kategori=satir["kategori"],
        oncelik=satir["oncelik"],
        durum=satir["durum"],
        acilis_zamani=satir["acilis_zamani"],
        cevap_suresi_sn=satir["cevap_suresi_sn"],
        kapanis_zamani=satir["kapanis_zamani"],
        temsilci_id=satir["temsilci_id"],
        notlar=satir["notlar"] or "",
    )


def _satirdan_temsilci(satir: sqlite3.Row) -> Temsilci:
    return Temsilci(
        id=satir["id"],
        ad=satir["ad"],
        beceriler=satir["beceriler"].split(","),
        vardiya=satir["vardiya"],
        aktif=bool(satir["aktif"]),
    )


def cagri_listele(durum: str = None, limit: int = 50) -> List[Cagri]:
    conn = baglanti_al()
    if durum:
        sorgu = "SELECT * FROM cagrilar WHERE durum = '" + durum + "' ORDER BY id DESC LIMIT " + str(limit)
        satirlar = conn.execute(sorgu).fetchall()
    else:
        satirlar = conn.execute(
            "SELECT * FROM cagrilar ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_satirdan_cagri(s) for s in satirlar]


def cagri_getir(cagri_id: int) -> Optional[Cagri]:
    satir = baglanti_al().execute(
        "SELECT * FROM cagrilar WHERE id = ?", (cagri_id,)
    ).fetchone()
    return _satirdan_cagri(satir) if satir else None


def cagri_ekle(cagri: Cagri) -> Cagri:
    conn = baglanti_al()
    imlec = conn.execute(
        """
        INSERT INTO cagrilar (musteri_ad, musteri_telefon, musteri_eposta,
                              kategori, oncelik, durum, acilis_zamani,
                              cevap_suresi_sn, kapanis_zamani, temsilci_id, notlar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cagri.musteri_ad, cagri.musteri_telefon, cagri.musteri_eposta,
            cagri.kategori, cagri.oncelik, cagri.durum, cagri.acilis_zamani,
            cagri.cevap_suresi_sn, cagri.kapanis_zamani, cagri.temsilci_id,
            cagri.notlar,
        ),
    )
    conn.commit()
    cagri.id = imlec.lastrowid
    return cagri


def cagri_durum_degistir(cagri_id: int, yeni_durum: str,
                         kapanis_zamani: str = None) -> Cagri:
    cagri = cagri_getir(cagri_id)
    if cagri is None:
        raise LookupError("Cagri bulunamadi: %s" % cagri_id)
    if not durum_gecisi_gecerli_mi(cagri.durum, yeni_durum):
        raise ValueError(
            "Gecersiz durum gecisi: %s -> %s" % (cagri.durum, yeni_durum)
        )
    conn = baglanti_al()
    conn.execute(
        "UPDATE cagrilar SET durum = ?, kapanis_zamani = ? WHERE id = ?",
        (yeni_durum, kapanis_zamani, cagri_id),
    )
    conn.commit()
    return cagri_getir(cagri_id)


def cagri_ata(cagri_id: int, temsilci_id: int) -> Cagri:
    cagri = cagri_getir(cagri_id)
    if cagri is None:
        raise LookupError("Cagri bulunamadi: %s" % cagri_id)
    if not durum_gecisi_gecerli_mi(cagri.durum, "atandi"):
        raise ValueError("Cagri atanabilir durumda degil: %s" % cagri.durum)
    conn = baglanti_al()
    conn.execute(
        "UPDATE cagrilar SET durum = 'atandi', temsilci_id = ? WHERE id = ?",
        (temsilci_id, cagri_id),
    )
    conn.commit()
    return cagri_getir(cagri_id)


def temsilci_listele(sadece_aktif: bool = True) -> List[Temsilci]:
    conn = baglanti_al()
    if sadece_aktif:
        satirlar = conn.execute(
            "SELECT * FROM temsilciler WHERE aktif = 1 ORDER BY id"
        ).fetchall()
    else:
        satirlar = conn.execute("SELECT * FROM temsilciler ORDER BY id").fetchall()
    return [_satirdan_temsilci(s) for s in satirlar]


def temsilci_getir(temsilci_id: int) -> Optional[Temsilci]:
    satir = baglanti_al().execute(
        "SELECT * FROM temsilciler WHERE id = ?", (temsilci_id,)
    ).fetchone()
    return _satirdan_temsilci(satir) if satir else None


def temsilci_acik_yuku(temsilci_id: int) -> int:
    """Temsilcinin üzerindeki kapanmamış çağrı sayısı."""
    satir = baglanti_al().execute(
        "SELECT COUNT(*) AS adet FROM cagrilar "
        "WHERE temsilci_id = ? AND durum != 'kapandi'",
        (temsilci_id,),
    ).fetchone()
    return satir["adet"]
