<!-- Capstone görevinin işlevsel spec'i: Temsilci Performans Raporu (A2 + A3 sözleşmesi). -->

# CAPSTONE-SPEC — Temsilci Performans Raporu

> Bu doküman, "Capstone: Vardiya Sonu Teslimi" görevinin İŞLEVSEL sözleşmesidir.
> Kabul ölçütü: `tests/capstone/` altındaki testler + `araclar/capstone_denetim.py` kapıları.
> Test seti ile bu spec çelişirse **SPEC KAZANIR** (bkz. CAPSTONE.md, aşama A3).

## Amaç

Vardiya sonunda ekip lideri, bir temsilcinin performansını tek istekle görmek
istiyor: kaç çağrıya baktı, ortalama ne kadar sürede cevapladı, SLA'ya ne kadar
uydu. Bugün bu bilgi ancak `/rapor/sla` (tüm merkez) üzerinden dolaylı görülüyor;
temsilci bazlı görünürlük yok.

## Bölüm 1 — JSON rapor (Aşama A2)

`GET /rapor/temsilci/{id}`

Başarılı yanıt gövdesi (200):

```json
{"rapor": {
  "temsilci_id": 1,
  "ad": "Deniz Acar",
  "cagri_sayisi": 26,
  "ortalama_cevap_sn": 12.0,
  "sla_uyum_yuzde": 92.0
}}
```

| Alan | Tip | Tanım |
|---|---|---|
| `temsilci_id` | int | istenen temsilcinin id'si |
| `ad` | str | `temsilciler` tablosundaki ad |
| `cagri_sayisi` | int | `temsilci_id` bu temsilci olan TÜM çağrılar |
| `ortalama_cevap_sn` | float | `cevap_suresi_sn` dolu çağrıların ortalaması, `round(x, 1)` |
| `sla_uyum_yuzde` | float | `cevap_suresi_sn` dolu çağrılar içinde süresi `ayarlar.SLA_CEVAP_SANIYE` değerini aşmayanların yüzdesi, `round(x, 1)` |

Kurallar:

- `cevap_suresi_sn` dolu olmayan çağrılar ortalamaya ve uyum yüzdesine GİRMEZ;
  `cagri_sayisi`'na girer (çağrı temsilcinindir, henüz/hiç cevaplanmamıştır).
- SLA eşiği **`ayarlar.SLA_CEVAP_SANIYE`'den okunur**; sayıyı fonksiyon içine
  gömmek kabul edilmez (review'dan döner — `raporlama.py`'deki gömülü eşikler
  bilinen teknik borçtur, deseni kopyalama).
- Çözüm süresi (kapanış − açılış) bu raporun kapsamı DIŞINDADIR.
- İşleyici sözleşmesi: `cagriops/api.py` içine
  `def temsilci_raporu(temsilci_id: int, parametreler: dict = None)` →
  `(durum_kodu, govde)` döndürür; rota `sunucu.ROTALAR` tablosuna eklenir.
  (İkinci parametre Bölüm 2'de kullanılacak; A2'de vermesen de olur.)

## Bölüm 2 — CSV çıktısı ve SLA uyarısı (Aşama A3)

1. JSON gövdesine `sla_uyari` (bool) alanı eklenir:
   `sla_uyum_yuzde` **%90'ın ALTINDA** ise `true`, değilse `false`.
   Uyarı eşiği `ayarlar.py`'ye `SLA_UYARI_YUZDE = 90.0` olarak eklenir ve
   oradan okunur.
2. `?format=csv` verilirse gövde CSV metnidir (`str`):
   - Başlık satırı, alan adlarıyla birebir:
     `temsilci_id,ad,cagri_sayisi,ortalama_cevap_sn,sla_uyum_yuzde,sla_uyari`
   - Tek veri satırı; ayraç virgül; değeri olmayan hücre boş bırakılır;
     bool değerler küçük harf `true` / `false`.
   - `format` parametresi `csv` dışında bir değerse veya hiç verilmezse JSON dönülür.
3. **Sunucu katmanı görevi:** mevcut dağıtım katmanı (`sunucu._dagit`) id alan
   rotalara query parametrelerini GEÇİRMEZ ve yalnızca JSON gövde yazar.
   Bu aşamada `cagriops/sunucu.py` iki yönde genişletilmelidir:
   1. id alan rotada işleyici iki parametre kabul ediyorsa
      (`isleyici.__code__.co_argcount == 2`) çağrı
      `isleyici(int(id), parametreler)` olur — tek parametreli mevcut
      işleyiciler etkilenmez.
   2. İşleyici gövdesi `str` döndürürse yanıt
      `text/csv; charset=utf-8` içerik tipiyle yazılır.

## Kapsam sınırları

- Mevcut endpoint davranışları ve `yonlendirme.py` puanlaması DEĞİŞMEZ.
- Yeni bağımlılık eklenmez (yalnızca standart kütüphane).
- UI yok; çıktılar JSON/CSV.

## Kabul

```bash
python tests/capstone/test_a2_cekirdek.py   # Aşama A2
python tests/capstone/test_a3_csv_sla.py    # Aşama A3
python araclar/capstone_denetim.py --asama 2
python araclar/capstone_denetim.py --asama 3
```
