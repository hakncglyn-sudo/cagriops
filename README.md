# CagriOps

Kurgusal bir çağrı merkezinin operasyon servisi: çağrı kayıtları, temsilci
yönetimi, kural tabanlı çağrı yönlendirme ve SLA raporları. Tüm veri
sentetiktir; gerçek kişi veya kurum bilgisi içermez.

## Kurulum ve çalıştırma

Tek önkoşul: **Python 3.10+** (ek paket gerekmez, her şey standart kütüphane).

```bash
git clone https://github.com/hakncglyn-sudo/cagriops.git
cd cagriops
python app.py
```

Servis `http://127.0.0.1:8765` adresinde açılır. Örnek veri repoyla birlikte
gelir (`data/cagrilar.db`); bozulursa yeniden üretebilirsiniz:

```bash
python araclar/seed_uret.py
```

Testler:

```bash
python -m unittest discover -s tests
```

> Eğitim capstone görevi: [katilimci/CAPSTONE.md](katilimci/CAPSTONE.md)

## Endpoint'ler

| Metot | Yol | Açıklama |
|---|---|---|
| GET | `/cagrilar?durum=acik&limit=20` | Çağrı listesi (durum filtresi opsiyonel) |
| GET | `/cagrilar/<id>` | Çağrı detayı |
| POST | `/cagrilar` | Yeni çağrı aç (JSON gövde) |
| POST | `/cagrilar/<id>/yonlendir` | Çağrıyı en uygun temsilciye ata |
| POST | `/cagrilar/<id>/kapat` | Çağrıyı kapat |
| GET | `/temsilciler` | Aktif temsilciler (`?hepsi=1` ile tümü) |
| GET | `/temsilciler/<id>` | Temsilci detayı + üzerindeki açık yük |
| GET | `/rapor/sla` | SLA özet raporu |
| GET | `/rapor/bekleyenler?adet=5` | En uzun bekleyen açık çağrılar |

Yeni çağrı örneği:

```bash
curl -X POST http://127.0.0.1:8765/cagrilar \
  -H "Content-Type: application/json" \
  -d '{"musteri_ad":"Ayşe Yılmaz","musteri_telefon":"05001234567","musteri_eposta":"ayse@ornekmail.com","kategori":"ariza","oncelik":"yuksek"}'

curl -X POST http://127.0.0.1:8765/cagrilar/221/yonlendir
```

## Proje yapısı

```
app.py                  # giriş noktası
cagriops/
  sunucu.py             # HTTP rota tablosu ve istek dağıtımı
  api.py                # endpoint işleyicileri
  yonlendirme.py        # çağrı yönlendirme kural motoru (puanlama)
  raporlama.py          # SLA ve operasyon istatistikleri
  depo.py               # SQLite erişim katmanı
  modeller.py           # veri modelleri ve doğrulama
  kayitci.py            # loglama (loglar/cagriops.log)
  ayarlar.py            # sabitler
data/cagrilar.db        # sentetik örnek veri
araclar/seed_uret.py    # veriyi sıfırdan üretir
tests/                  # birim testleri
tmp/                    # eski rapor çıktıları
```

## Alan kuralları (kısa)

- Çağrı durumları: `acik → atandi → beklemede → kapandi` (geçiş kuralları
  `modeller.py` içinde).
- Yönlendirme puanı: beceri eşleşmesi + öncelik ağırlığı − açık yük cezası;
  vardiya dışı temsilci yalnızca kritik çağrıda değerlendirilir.
- SLA: cevap ≤ 20 sn, çözüm ≤ 15 dk.
