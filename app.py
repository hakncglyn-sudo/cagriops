"""CagriOps giriş noktası.

Çalıştırma:
    python app.py
"""

import os
import sys

from cagriops import ayarlar, sunucu


def main() -> int:
    if not os.path.exists(ayarlar.DB_YOLU):
        print("Veritabani bulunamadi: %s" % ayarlar.DB_YOLU)
        print("Once sentetik veriyi uretin: python araclar/seed_uret.py")
        return 1

    print("CagriOps %s — http://%s:%s" % (ayarlar.SURUM, ayarlar.HOST, ayarlar.PORT))
    print("Durdurmak icin Ctrl+C")
    sunucu.calistir()
    return 0


if __name__ == "__main__":
    sys.exit(main())
