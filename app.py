# firebase_config.py
import firebase_admin
from firebase_admin import credentials, db, firestore, auth
from firebase_admin.exceptions import FirebaseError
from dotenv import load_dotenv
import os
import logging

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment değişkenlerini yükle
load_dotenv()

def initialize_firebase() -> db.Reference | None:
    """
    Firebase'i başlatır ve Realtime Database root referansını döndürür.
    
    Returns:
        db.Reference | None: Firebase root referansı veya hata durumunda None
    """
    try:
        # Firebase zaten başlatılmışsa önbelleği temizle
        if firebase_admin._apps:
            firebase_admin.delete_app(firebase_admin.get_app())
            logger.warning("Mevcut Firebase uygulaması temizlendi")

        # Gerekli environment değişkenlerini kontrol et
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "cman-smartasst-firebase-adminsdk-fbsvc-0f0ef0dc8e.json")
        database_url = os.getenv("FIREBASE_DB_URL")
        
        if not database_url:
            raise ValueError("FIREBASE_DB_URL environment değişkeni tanımlı değil")
            
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Service account dosyası bulunamadı: {service_account_path}")

        # Firebase'i başlat
        cred = credentials.Certificate(service_account_path)
        firebase_app = firebase_admin.initialize_app(cred, {
            'databaseURL': database_url
        })
        
        # Ek servisleri başlat (Firestore ve Auth)
        firestore_client = firestore.client()
        auth_client = auth
        
        logger.info("✅ Firebase başarıyla başlatıldı")
        logger.info(f"Kullanılan Database URL: {database_url}")
        
        return db.reference('/')
    
    except (ValueError, FileNotFoundError) as e:
        logger.error(f"❌ Konfigürasyon hatası: {str(e)}")
        return None
    except FirebaseError as e:
        logger.error(f"❌ Firebase hatası: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Beklenmeyen hata: {str(e)}", exc_info=True)
        return None

# Firebase'i başlat ve root referansı al
root_ref = initialize_firebase()

# Firestore ve Auth istemcilerini global olarak kullanıma sun
firestore_db = firestore.client() if root_ref else None
auth_client = auth if root_ref else None