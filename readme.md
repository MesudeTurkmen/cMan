CMAN/  
├── app.py                  # Flask ana uygulama  
├── config.py               # API key'ler, veritabanı bağlantısı  
├── requirements.txt        # Gereken kütüphaneler  
├── models/  
│   ├── user.py             # Kullanıcı modeli (ad, email, konum, sağlık verisi)  
│   ├── notification.py    # Bildirim geçmişi (tür, içerik, zaman)  
│   └── partnership.py     # Anlaşmalı şirketler (isim, kampanya, koordinatlar)  
├── routes/  
│   ├── auth.py             # Kullanıcı giriş/kayıt  
│   ├── weather.py          # Hava durumu API entegrasyonu  
│   ├── health.py           # Giyilebilir cihaz verileri ve 112 çağrısı  
│   ├── municipality.py     # Belediye veri çekme ve bildirim  
│   └── partners.py         # Anlaşmalı şirketlerin kampanyaları   
├── utils/  
│   ├── emergency.py        # 112 çağrı ve sağlık algoritmaları  
│   └── location_helper.py  # Konum tabanlı öneri motoru  
└── tests/                  # Unit testler  


## kullanıcı tercihine göre sabah/akşam hava durumu (OpenWeatherMap API)
## Ani Değişimlerde Acil Uyarı
## Giyilebilir Cihaz Entegrasyonu
## Belediye Verileri
## Şirket İş Birlikleri ve Gelir Modeli