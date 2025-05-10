from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, auth, firestore, db
from firebase_admin.exceptions import FirebaseError
from dotenv import load_dotenv
import os
import logging

# Loglama ve Environment Yapılandırması
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#######################3
from gunicorn.app.base import BaseApplication

class FlaskApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load(self):
        return self.application

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

# Firebase'i burada başlat (Gunicorn worker'larından ÖNCE)
try:
    # Environment değişkenlerini yükle
    from dotenv import load_dotenv
    load_dotenv()

    FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")

    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
    firebase_app = firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })
    logger.info("✅ Firebase başlatıldı (Gunicorn öncesi)")
except Exception as e:
    logger.error(f"❌ Firebase başlatılamadı: {str(e)}")
    raise SystemExit(1)  # Uygulamayı durdur
#######################



# Flask Uygulamasını Başlat
app = Flask(__name__)

# Firebase Başlatma
try:
    # Gerekli environment değişkenlerini kontrol et
    FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    FIREBASE_DB_URL = os.getenv("FIREBASE_DB_URL")
    
    if not all([FIREBASE_SERVICE_ACCOUNT, FIREBASE_DB_URL]):
        raise ValueError("Firebase environment değişkenleri eksik")

    # Önceki bağlantıları temizle
    if firebase_admin._apps:
        firebase_admin.delete_app(firebase_admin.get_app())
        logger.info("Önceki Firebase bağlantısı temizlendi")

    # Firebase'i başlat
    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT)
    firebase_app = firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })
    
    # Servisleri başlat
    firestore_db = firestore.client()
    realtime_db = db.reference('/')
    logger.info("✅ Firebase servisleri başlatıldı")

except (ValueError, FileNotFoundError) as e:
    logger.error(f"❌ Konfigürasyon hatası: {str(e)}")
    firestore_db = None
    realtime_db = None
except FirebaseError as e:
    logger.error(f"❌ Firebase hatası: {str(e)}")
    firestore_db = None
    realtime_db = None
except Exception as e:
    logger.error(f"❌ Kritik hata: {str(e)}", exc_info=True)
    firestore_db = None
    realtime_db = None

'''# Route'lar
@app.route('/signup', methods=['POST'])
def signup():
    if not firestore_db:
        return jsonify({"error": "Firebase bağlantı hatası"}), 500

    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Kullanıcı oluştur
        user = auth.create_user(email=email, password=password)
        
        # Firestore'a kaydet
        firestore_db.collection('users').document(user.uid).set({
            'email': email,
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({
            "uid": user.uid,
            "email": user.email,
            "message": "Kayıt başarılı"
        }), 200

    except auth.EmailAlreadyExistsError:
        return jsonify({"error": "Bu email zaten kayıtlı"}), 400
    except Exception as e:
        logger.error(f"Kayıt hatası: {str(e)}")
        return jsonify({"error": "Sunucu hatası"}), 500

@app.route('/login', methods=['POST'])
def login():
    if not firestore_db:
        return jsonify({"error": "Firebase bağlantı hatası"}), 500

    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Kullanıcıyı doğrula
        user = auth.get_user_by_email(email)
        return jsonify({
            "uid": user.uid,
            "email": user.email,
            "message": "Giriş başarılı"
        }), 200

    except auth.UserNotFoundError:
        return jsonify({"error": "Kullanıcı bulunamadı"}), 404
    except Exception as e:
        logger.error(f"Giriş hatası: {str(e)}")
        return jsonify({"error": "Sunucu hatası"}), 500

#@app.route('/verify', methods=['POST'])
#def verify_token():
    try:
        # Get ID token from the 'Authorization' header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401

        id_token = auth_header.split('Bearer ')[1]

        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']

        # You can fetch additional user details (optional)
        user = auth.get_user(uid)

        return jsonify({
            'message': 'Token is valid',
            'uid': uid,
            'email': user.email,
            'name': user.display_name
        }), 200

    except FirebaseError as e:
        return jsonify({'error': f'Firebase error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500
'''
@app.route('/verify', methods=['POST'])
def verify_token():
    try:
        auth_header = request.headers.get('Authorization')
        logger.info(f"Authorization header: {auth_header}")  # Log it

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401

        id_token = auth_header.split('Bearer ')[1]
        logger.info(f"ID token received: {id_token[:20]}...")  # Log the first part only

        decoded_token = auth.verify_id_token(id_token)
        logger.info(f"Decoded token: {decoded_token}")

        uid = decoded_token['uid']
        user = auth.get_user(uid)
        logger.info(f"User email: {user.email}")

        return jsonify({
            'message': 'Token is valid',
            'uid': uid,
            'email': user.email,
            'name': user.display_name or ""
        }), 200

    except FirebaseError as e:
        logger.error(f"Firebase error: {str(e)}", exc_info=True)
        return jsonify({'error': f'Firebase error: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"message": "Merhaba AWS!"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)