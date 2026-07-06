# Capstone denetçisi: aşama kapılarını tek komutla doğrular (kullanım: katilimci/CAPSTONE.md).
"""
Kullanım:
    python araclar/capstone_denetim.py --asama N     # tek aşamanın kapısı (N: 0-6)
    python araclar/capstone_denetim.py               # tüm kapılar + TESLİM RAPORU
    python araclar/capstone_denetim.py --kurulum-testi   # altyapı doğrulaması (eğitim öncesi)
Exit 0 = geçti, 1 = kaldı.
"""

import argparse
import glob
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
A2_TEST = os.path.join("tests", "capstone", "test_a2_cekirdek.py")
A3_TEST = os.path.join("tests", "capstone", "test_a3_csv_sla.py")

_CEVIRI = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")


def normalize(metin: str) -> str:
    return metin.translate(_CEVIRI).lower()


def oku(yol: str) -> str:
    with open(yol, encoding="utf-8", errors="replace") as dosya:
        return dosya.read()


def komut(args):
    return subprocess.run(
        args, cwd=REPO, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def test_kos(gorel_yol: str) -> subprocess.CompletedProcess:
    return komut([sys.executable, gorel_yol])


def discover_kos():
    """(exit_kodu, kosulan_test_sayisi) döndürür."""
    sonuc = komut([sys.executable, "-m", "unittest", "discover", "-s", "tests"])
    metin = (sonuc.stdout or "") + (sonuc.stderr or "")
    eslesme = re.search(r"Ran (\d+) tests?", metin)
    return sonuc.returncode, (int(eslesme.group(1)) if eslesme else 0)


def kanit_bolumu(baslik: str):
    """KANIT.md'den '## <baslik>' bölümünü döndürür (HTML yorumları sökülmüş)."""
    yol = os.path.join(REPO, "KANIT.md")
    if not os.path.exists(yol):
        return None
    icerik = re.sub(r"<!--.*?-->", "", oku(yol), flags=re.S)
    eslesme = re.search(
        r"^##\s*%s\b.*?(?=^##\s|\Z)" % re.escape(baslik),
        icerik, re.S | re.M,
    )
    return eslesme.group(0) if eslesme else None


# ---------------------------------------------------------------- HTTP smoke

def _bos_port() -> int:
    for aday in (8791, 8793, 8797):
        with socket.socket() as soket:
            try:
                soket.bind(("127.0.0.1", aday))
                return aday
            except OSError:
                continue
    return 0


def _http_al(adres: str):
    """(durum_kodu, icerik_tipi, govde_metni) döndürür; bağlantı hatasında (0, '', '')."""
    try:
        with urllib.request.urlopen(adres, timeout=3) as yanit:
            return yanit.status, yanit.headers.get("Content-Type", ""), yanit.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as hata:
        return hata.code, hata.headers.get("Content-Type", ""), ""
    except (urllib.error.URLError, OSError):
        return 0, "", ""


def http_smoke(csv_kontrol: bool):
    """Sunucuyu ayrı süreçte kaldırıp uç noktaları canlı dener; [(ok, mesaj)] döndürür."""
    port = _bos_port()
    if not port:
        return [(False, "HTTP smoke: uygun port bulunamadı (8791/8793/8797 dolu)")]
    surec = subprocess.Popen(
        [sys.executable, "-c",
         "from cagriops import sunucu; sunucu.calistir(port=%d)" % port],
        cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    taban = "http://127.0.0.1:%d" % port
    sonuclar = []
    try:
        ayakta = False
        for _ in range(40):
            durum, _tip, _govde = _http_al(taban + "/rapor/sla")
            if durum:
                ayakta = True
                break
            time.sleep(0.25)
        if not ayakta:
            return [(False, "HTTP smoke: sunucu %s üzerinde ayağa kalkmadı" % taban)]

        durum, _tip, govde = _http_al(taban + "/rapor/temsilci/1")
        sonuclar.append((durum == 200 and '"rapor"' in govde,
                         "GET /rapor/temsilci/1 → 200 + \"rapor\" gövdesi (canlı: %s)" % durum))
        durum, _tip, _govde = _http_al(taban + "/rapor/temsilci/9999")
        sonuclar.append((durum == 404,
                         "GET /rapor/temsilci/9999 → 404 (canlı: %s)" % durum))
        if csv_kontrol:
            durum, tip, _govde = _http_al(taban + "/rapor/temsilci/1?format=csv")
            sonuclar.append((durum == 200 and tip.startswith("text/csv"),
                             "GET ?format=csv → 200 + text/csv (canlı: %s, %s)" % (durum, tip or "-")))
    finally:
        surec.terminate()
        try:
            surec.wait(timeout=3)
        except subprocess.TimeoutExpired:
            surec.kill()
    return sonuclar


# ---------------------------------------------------------------- Kapılar

def kapi_a0():
    kontroller = []
    branch = komut(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    kontroller.append((branch.startswith("capstone/"),
                       "Branch 'capstone/' önekli (şu an: %s)" % (branch or "?")))
    if branch == "capstone/adsoyad":
        kontroller.append((False, "Branch adına KENDİ adını yaz (capstone/adsoyad kalmış)"))
    kirli = komut(["git", "status", "--porcelain"]).stdout.strip()
    kontroller.append((kirli == "", "Çalışma ağacı temiz (git status)"))
    return kontroller


def kapi_a1():
    kontroller = []
    bolum = kanit_bolumu("A1")
    kontroller.append((bolum is not None, "KANIT.md kökte ve '## A1' bölümü dolu"))
    if bolum:
        sorular = [s for s in bolum.splitlines() if s.strip().endswith("?")]
        kontroller.append((len(sorular) >= 2,
                           "A1 altında soru olarak yazılmış en az 2 satır (bulunan: %d)" % len(sorular)))
        icerik_satirlari = [s for s in bolum.splitlines()[1:]
                            if s.strip() and not s.strip().startswith("#")]
        kontroller.append((len(icerik_satirlari) >= 3 and "varsayim" in normalize(bolum),
                           "A1 altında varsayımlar + sorular dolu (başlık saymaz; içerik: %d satır)"
                           % len(icerik_satirlari)))
    return kontroller


def kapi_a2(smoke=True):
    kontroller = []
    sonuc = test_kos(A2_TEST)
    kontroller.append((sonuc.returncode == 0, "A2 kabul testleri yeşil (%s)" % A2_TEST))
    if smoke:
        kontroller.extend(http_smoke(csv_kontrol=False))
    return kontroller


def kapi_a3(smoke=True):
    kontroller = []
    sonuc = test_kos(A3_TEST)
    kontroller.append((sonuc.returncode == 0, "A3 kabul testleri yeşil (%s)" % A3_TEST))
    test_sayisi = len(re.findall(r"^\s*def test_", oku(os.path.join(REPO, A3_TEST)), re.M))
    kontroller.append((test_sayisi >= 5,
                       "A3 dosyasında en az 5 test duruyor (silmek yok; bulunan: %d)" % test_sayisi))
    loglar = komut(["git", "log", "--pretty=%s"]).stdout.splitlines()
    duzeltme = any(normalize(satir).strip().startswith("test duzeltme") for satir in loglar)
    kontroller.append((duzeltme, "git log'da 'test düzeltme:' önekli gerekçeli commit"))
    if smoke:
        kontroller.extend(http_smoke(csv_kontrol=True))
    ayarlar_icerik = oku(os.path.join(REPO, "cagriops", "ayarlar.py"))
    if "SLA_UYARI" not in ayarlar_icerik:
        print("  [i] Uyarı: ayarlar.py içinde SLA_UYARI_* sabiti görünmüyor — eşik nereden okunuyor?")
    return kontroller


def kapi_a4():
    kontroller = []
    bolum = kanit_bolumu("A4")
    kontroller.append((bolum is not None, "KANIT.md'de '## A4' bölümü dolu"))
    if bolum:
        norm = normalize(bolum)
        kontroller.append(("diff-reviewer" in norm, "A4'te diff-reviewer raporu özeti var"))
        blok_var = any(k in norm for k in
                       ("blokland", "engellend", "blocked", "reddedild", "izin verilmedi"))
        kontroller.append((blok_var, "A4'te hook fren kanıtı var (blok mesajı yapıştırılmış)"))
    skiller = glob.glob(os.path.join(REPO, ".claude", "skills", "*", "SKILL.md"))
    kontroller.append((len(skiller) >= 1, ".claude/skills/ altında en az 1 skill"))
    agentlar = glob.glob(os.path.join(REPO, ".claude", "agents", "*.md"))
    kontroller.append((len(agentlar) >= 1, ".claude/agents/ altında en az 1 subagent"))
    settings_yolu = os.path.join(REPO, ".claude", "settings.json")
    hook_dosyalari = glob.glob(os.path.join(REPO, ".claude", "hooks", "*.py"))
    hook_var = (os.path.exists(settings_yolu) and "hooks" in oku(settings_yolu)) or hook_dosyalari
    kontroller.append((bool(hook_var), "Hook kurulu (.claude/settings.json 'hooks' veya .claude/hooks/*.py)"))
    return kontroller


def kapi_a5():
    kontroller = []
    kontroller.append((test_kos(A2_TEST).returncode == 0, "A2 kabul testleri yeşil"))
    kontroller.append((test_kos(A3_TEST).returncode == 0, "A3 kabul testleri yeşil"))
    kod, adet = discover_kos()
    kontroller.append((kod == 0 and adet >= 17,
                       "Mevcut test paketi yeşil (Ran %d, en az 17 olmalı)" % adet))
    return kontroller


def kapi_a6():
    kontroller = []
    bolum = kanit_bolumu("A6")
    kontroller.append((bolum is not None, "KANIT.md'de '## A6' teslim özeti var"))
    if bolum:
        satirlar = [s for s in bolum.splitlines()[1:]
                    if s.strip() and not s.strip().startswith("#")]
        kontroller.append((len(satirlar) >= 3,
                           "A6 özeti en az 3 satır (bulunan: %d)" % len(satirlar)))
    son_mesaj = komut(["git", "log", "-1", "--pretty=%s"]).stdout.strip()
    kontroller.append((len(son_mesaj) >= 15 and " " in son_mesaj,
                       "Son commit mesajı anlamlı (şu an: %r)" % (son_mesaj[:50] or "?")))
    kirli = komut(["git", "status", "--porcelain"]).stdout.strip()
    kontroller.append((kirli == "", "Çalışma ağacı temiz — her şey commit'lendi"))
    return kontroller


KAPILAR = [
    ("A0", "Hazırlık", kapi_a0),
    ("A1", "Plan Kapısı", kapi_a1),
    ("A2", "Çekirdek (TDD)", kapi_a2),
    ("A3", "CSV + SLA Uyarısı", kapi_a3),
    ("A4", "Kendi Araçlarınla Denetim", kapi_a4),
    ("A5", "/goal Koşusu", kapi_a5),
    ("A6", "Teslim", kapi_a6),
]


def kontrolleri_yazdir(kontroller) -> bool:
    hepsi = True
    for ok, mesaj in kontroller:
        print("  [%s] %s" % ("OK" if ok else " X", mesaj))
        hepsi = hepsi and ok
    return hepsi


def asama_kos(numara: int) -> int:
    ad, baslik, kapi = KAPILAR[numara]
    print("— %s · %s —" % (ad, baslik))
    gecti = kontrolleri_yazdir(kapi())
    print()
    if gecti:
        print("%s KAPISI: GEÇTİN ✓ — sonraki aşamaya geçebilirsin." % ad)
        return 0
    print("%s KAPISI: KALDIN — yukarıda [ X] işaretli eksikleri tamamla." % ad)
    return 1


def teslim_raporu() -> int:
    sonuclar = []
    for ad, baslik, kapi in KAPILAR:
        print("— %s · %s —" % (ad, baslik))
        gecti = kontrolleri_yazdir(kapi())
        sonuclar.append((ad, baslik, gecti))
        print()
    gecen = sum(1 for _, _, g in sonuclar if g)
    yuzde = round(gecen * 100 / len(sonuclar))
    branch = komut(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    son_commit = komut(["git", "log", "-1", "--pretty=%h %s"]).stdout.strip()

    genislik = 58
    def satir(metin=""):
        print("║ " + metin.ljust(genislik - 4) + " ║")
    print("╔" + "═" * (genislik - 2) + "╗")
    satir("CAPSTONE · VARDİYA SONU TESLİMİ — TESLİM RAPORU")
    print("╠" + "═" * (genislik - 2) + "╣")
    for ad, baslik, gecti in sonuclar:
        durum = "GEÇTİ ✓" if gecti else "KALDI ✗"
        satir("%s %-28s %s" % (ad, baslik, durum))
    print("╠" + "═" * (genislik - 2) + "╣")
    satir("İlerleme: %%%d (%d/%d kapı)" % (yuzde, gecen, len(sonuclar)))
    satir("Branch  : %s" % (branch or "?"))
    satir("Commit  : %s" % (son_commit[: genislik - 14] or "?"))
    print("╚" + "═" * (genislik - 2) + "╝")
    if gecen == len(sonuclar):
        print("TESLİME HAZIR ✓ — bu ekranı showcase'de göster.")
        return 0
    print("Henüz teslim edilemez — kalan kapılar için --asama N ile detaya in.")
    return 1


# ---------------------------------------------------------------- Kurulum testi

def kurulum_testi() -> int:
    kontroller = []

    gerekli = [
        os.path.join("katilimci", "CAPSTONE.md"),
        os.path.join("katilimci", "CAPSTONE-SPEC.md"),
        os.path.join("katilimci", "KANIT-SABLON.md"),
        A2_TEST, A3_TEST,
        os.path.join("araclar", "capstone_denetim.py"),
    ]
    for gorel in gerekli:
        kontroller.append((os.path.exists(os.path.join(REPO, gorel)), "Dosya var: %s" % gorel))
    kontroller.append(("CAPSTONE.md" in oku(os.path.join(REPO, "README.md")),
                       "README.md capstone'a işaret ediyor"))

    kod, adet = discover_kos()
    kontroller.append((kod == 0 and adet == 17,
                       "unittest discover -s tests → tam 17 test yeşil (Ran %d, exit %d)" % (adet, kod)))
    for gorel in (os.path.join("tests", "__init__.py"),
                  os.path.join("tests", "capstone", "__init__.py")):
        kontroller.append((not os.path.exists(os.path.join(REPO, gorel)),
                           "%s YOK (discover izolasyonu)" % gorel))

    api_icerik = oku(os.path.join(REPO, "cagriops", "api.py"))
    if "temsilci_raporu" not in api_icerik:
        kontroller.append((test_kos(A2_TEST).returncode != 0, "A2 temiz repoda KIRMIZI (beklenen)"))
        kontroller.append((test_kos(A3_TEST).returncode != 0, "A3 temiz repoda KIRMIZI (beklenen)"))
    else:
        print("  [i] api.temsilci_raporu mevcut — uygulama başlamış, KIRMIZI kontrolü atlandı.")

    a3_icerik = oku(os.path.join(REPO, A3_TEST))
    isaret = "yaygin SLA hedefi %" + "9" + "5"
    kontroller.append((isaret in a3_icerik and "def test_sla_uyari_sinir_kontrolu" in a3_icerik,
                       "A3 sınır kontrolü testi yerinde"))

    kontroller.extend(_icerik_taramasi())

    print("— Kurulum testi —")
    gecti = kontrolleri_yazdir(kontroller)
    print()
    print("KURULUM: %s" % ("TAMAM ✓" if gecti else "EKSİK — yukarıdaki [ X] maddeleri düzelt"))
    return 0 if gecti else 1


def _icerik_taramasi():
    """Yayın öncesi içerik temizliği: katılımcı dosyalarında olmaması gereken ifadeler."""
    kontroller = []
    genel_desenler = ["kasitli", "tuzak", "spoiler", "cevap anahtari",
                      "cozum rehberi", "hatali test", "bilerek", "egitmen", "bosluk"]
    md_desenler = [r"\b404\b", "bulunamadi", r"\b9" + r"5\b"]

    ihlaller = []
    md_dosyalar = glob.glob(os.path.join(REPO, "katilimci", "*.md"))
    test_dosyalar = glob.glob(os.path.join(REPO, "tests", "capstone", "*.py"))

    for yol in md_dosyalar + test_dosyalar:
        icerik = oku(yol)
        norm_satirlar = [normalize(s) for s in icerik.splitlines()]
        for no, satir in enumerate(norm_satirlar, 1):
            for desen in genel_desenler:
                if desen in satir:
                    ihlaller.append("%s:%d → '%s'" % (os.path.basename(yol), no, desen))
        if yol in md_dosyalar:  # sayısal/özel desenler yalnız katılımcı md'lerinde yasak
            for no, satir in enumerate(norm_satirlar, 1):
                for desen in md_desenler:
                    if re.search(desen, satir):
                        ihlaller.append("%s:%d → desen %s" % (os.path.basename(yol), no, desen))

    kontroller.append((not ihlaller,
                       "Katılımcı dosyalarında sızıntı yok" +
                       ("" if not ihlaller else " | " + " ; ".join(ihlaller[:6]))))
    return kontroller


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ayristirici = argparse.ArgumentParser(description="Capstone aşama denetçisi")
    ayristirici.add_argument("--asama", type=int, choices=range(0, 7),
                             help="tek aşamanın kapısını kontrol et (0-6)")
    ayristirici.add_argument("--kurulum-testi", action="store_true",
                             help="altyapının kendisini doğrula (eğitim öncesi)")
    argumanlar = ayristirici.parse_args()

    if argumanlar.kurulum_testi:
        return kurulum_testi()
    if argumanlar.asama is not None:
        return asama_kos(argumanlar.asama)
    return teslim_raporu()


if __name__ == "__main__":
    sys.exit(main())
