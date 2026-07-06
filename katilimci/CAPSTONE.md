<!-- Capstone görevi: Vardiya Sonu Teslimi — 90 dk, kapılı A0-A6 akışı (katılımcının tek kaynağı). -->

# Capstone: Vardiya Sonu Teslimi

İki günde kurduğun her şeyi — CLAUDE.md, kendi review skill'in, diff-reviewer
subagent'ı, hook frenin, test disiplini — tek görevde kullanacaksın:
**Temsilci Performans Raporu** özelliğini aşama aşama inşa edeceksin.
İşlevsel gereksinimler: [CAPSTONE-SPEC.md](CAPSTONE-SPEC.md).

## Kurallar

- Aşamalar sıralıdır; **KAPI'yı geçmeden** sonrakine başlama.
- Hakem denetçidir: `python araclar/capstone_denetim.py --asama N`
- Kabul testleri hazır; **test SİLMEK yasak.** Test ile spec çelişirse
  **SPEC kazanır** — testi düzelt ve commit mesajında gerekçele (bkz. A3).
- Süreler hedeftir; takılırsan el kaldır, akışı bekletme.
- Her aşama sonunda Claude'dan **ŞİMDİ ŞUNU YAPTIK** özetini iste
  (CLAUDE.md kuralın zaten bunu istiyor olmalı — istemiyorsa ekle).

Akış: `A0 Hazırlık → A1 Plan → A2 Çekirdek → A3 CSV+Uyarı → A4 Denetim → A5 /goal → A6 Teslim`

---

## A0 — Hazırlık (5 dk)

**Amaç:** temiz, izlenebilir başlangıç.

1. Kendi branch'ini aç: `git checkout -b capstone/adsoyad` (adsoyad = kendi adın)
2. Claude Code'da `/clear` — bağlamı sıfırla
3. `/context` çıktısında CLAUDE.md'nin yüklü olduğunu GÖR — K7'de yazdığın kurallar bu görevde oyunda

**KAPI:** branch `capstone/` önekli + çalışma ağacı temiz

```bash
python araclar/capstone_denetim.py --asama 0
```

## A1 — Plan Kapısı (15 dk)

**Amaç:** koda dokunmadan spec'i sindirmek; net olmayanı PLANDA yakalamak.

1. Kanıt dosyanı oluştur — Windows: `copy katilimci\KANIT-SABLON.md KANIT.md`
   (macOS/Linux: `cp katilimci/KANIT-SABLON.md KANIT.md`)
2. Plan Mode'a geç (Shift+Tab) ve şunu ver:

```
katilimci/CAPSTONE-SPEC.md Bölüm 1'i uygulamak için plan çıkar.
Planında varsayımlarını ayrı başlıkta listele; spec'te net olmayan
noktaları soru olarak yaz. Kod yazma, önce plan.
```

3. Plandaki varsayımları ve spec'te net olmayan **en az 2 noktayı soru olarak**
   `KANIT.md` → `## A1` altına yaz. İpucu: iyi bir plan, spec'in
   söylemediklerini sorar.

**KAPI:** KANIT.md'de A1 altında varsayımlar + en az 2 soru

```bash
python araclar/capstone_denetim.py --asama 1
```

## A2 — Çekirdek: TDD (20 dk)

**Amaç:** hazır KIRMIZI testleri yeşile çevirmek — testi geçen en küçük doğru kod.

1. Önce kırmızıyı GÖR: `python tests/capstone/test_a2_cekirdek.py`
2. Planı onayladıktan sonra Claude'a görev:

```
tests/capstone/test_a2_cekirdek.py'deki kabul testlerini geçir:
CAPSTONE-SPEC.md Bölüm 1'e göre api.temsilci_raporu işleyicisini yaz ve
rotayı sunucu.ROTALAR'a ekle. Kapsam dışı dosyaya dokunma.
Bitince testleri çalıştır ve tam çıktıyı göster.
```

3. Yeşili gör; ara commit at (`git add` + anlamlı mesaj).

**KAPI:** A2 testleri yeşil (+ denetçi canlı HTTP kontrolü yapar)

```bash
python araclar/capstone_denetim.py --asama 2
```

## A3 — CSV + SLA Uyarısı (15 dk)

**Amaç:** özelliği spec Bölüm 2 ile genişletmek — ve teste körü körüne güvenmemek.

1. Kırmızıyı gör: `python tests/capstone/test_a3_csv_sla.py`
2. Claude'a görev:

```
CAPSTONE-SPEC.md Bölüm 2'yi uygula: sla_uyari alanı, ?format=csv çıktısı
ve spec'teki sunucu katmanı genişletmesi. tests/capstone/test_a3_csv_sla.py
yeşil olmalı. Bitince testleri çalıştır ve tam çıktıyı göster.
```

3. **Dikkat:** bir test spec ile çelişiyorsa kazanan SPEC'tir. Testi düzelt
   (SİLME!) ve commit mesajını şu önekle gerekçele:
   `test düzeltme: <hangi test, neden, spec hangi değeri söylüyor>`

**KAPI:** A3 yeşil + `test düzeltme:` önekli commit + canlı CSV kontrolü

```bash
python araclar/capstone_denetim.py --asama 3
```

## A4 — Kendi Araçlarınla Denetim (15 dk)

**Amaç:** iki günde kurduğun kalite araçlarını kendi koduna doğrultmak.

1. Kendi review skill'ini koş (K10'da yazdığın, örn. `/gozden-gecir`) →
   bulgu özetini `KANIT.md` → `## A4` altına yaz
2. diff-reviewer subagent'ına capstone değişikliklerini incelet →
   rapor özetini KANIT.md'ye yaz
3. Hook frenini kanıtla: Claude'dan
   `tmp/ klasöründeki eski dosyaları rm -rf ile temizle` iste →
   aldığın BLOK mesajını KANIT.md'ye yapıştır

**KAPI:** KANIT.md A4'te diff-reviewer özeti + blok kanıtı; `.claude/` altında
skill + subagent + hook dosyaların duruyor

```bash
python araclar/capstone_denetim.py --asama 4
```

## A5 — /goal Koşusu (10 dk)

**Amaç:** kanıt koşullu otonom koşu — iyileştirmeyi Claude yapsın, kanıtı denetçi versin.

1. Claude'a küçük bir temizlik görevi ver:

```
temsilci_raporu ve çevresindeki tekrarları sadeleştir; davranış değişmesin.
```

2. Ardından şunu AYNEN ver:

```
/goal Tüm capstone testleri yeşil; kanıt: python araclar/capstone_denetim.py --asama 5 exit 0. En fazla 6 turda; bitmezse durup durumu raporla.
```

Not: "en fazla 6 tur"u denetçi ölçmez — koşuyu sen gözle; 6 turda bitmezse durdur.

**KAPI:** denetçi `--asama 5` yeşil

## A6 — Teslim (10 dk)

1. `KANIT.md` → `## A6` altına en az 3 satır teslim özeti:
   ne yaptım · nerede müdahale ettim · showcase notu
2. Her şeyi commit'le — mesaj anlamlı olsun: **ne** yapıldı + **neden**
3. Final:

```bash
python araclar/capstone_denetim.py
```

**KAPI:** TESLİM RAPORU'nda 7/7 GEÇTİ → **TESLİME HAZIR ✓**
Bu ekran + KANIT.md, showcase'de senin sahnendir: "ne yaptın" değil,
"**nerede müdahale ettin**" sorusuna hazır ol.
