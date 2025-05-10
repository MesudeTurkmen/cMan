# firebase_config.py
import firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    try:
        # Service Account dosyasını yükle
        cred = credentials.Certificate("cman-smartasst-firebase-adminsdk-fbsvc-0f0ef0dc8e.json")
        
        # Firebase'i başlat
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://cman-smartasst-default-rtdb.europe-west1.firebasedatabase.app'
        })
        print("✅ Firebase başarıyla başlatıldı!")
        return db.reference('/')  # Kök referansını döndür
    except Exception as e:
        print("❌ Firebase başlatılamadı:", str(e))
        return None

# Firebase'i başlat ve referansı al
root_ref = initialize_firebase()