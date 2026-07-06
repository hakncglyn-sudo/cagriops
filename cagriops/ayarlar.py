"""Uygulama ayarları."""

import os

SURUM = "1.4.2"

HOST = "127.0.0.1"
PORT = 8765

# Veritabanı dosyası (repo köküne göre)
DB_YOLU = os.path.join("data", "cagrilar.db")

# Dış CRM servisine yapılan sorgularda beklenecek süre (saniye).
TIMEOUT_SANIYE = 30

# SLA eşikleri
SLA_CEVAP_SANIYE = 20    # çağrı bu süre içinde cevaplanmalı
SLA_COZUM_DAKIKA = 15    # çağrı bu süre içinde çözülüp kapanmalı

LOG_DOSYASI = os.path.join("loglar", "cagriops.log")
