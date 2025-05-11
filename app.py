from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, auth, firestore, db
from firebase_admin.exceptions import FirebaseError
from dotenv import load_dotenv
import os
import logging
from routes.firebase_crud import *
from routes.weather import *
from routes.auth import *
from geopy import Nominatim

# Loglama ve Environment Yapılandırması
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_user(email):
    return db.reference(f'/users/{email}').get()

#konum doğrulama
# def validate_location(location: str) -> bool:
#     try:
#         geolocator = Nominatim(user_agent="weather_app")
#         return bool(geolocator.geocode(location))
#     except:
#         return False
# ----------------------------------
def validate_location(location: dict) -> bool:
    try:
        # Ensure the location contains 'latitude' and 'longitude'
        if 'latitude' not in location or 'longitude' not in location:
            return False

        latitude = location['latitude']
        longitude = location['longitude']

        # Check if latitude and longitude are within valid ranges
        if -90 <= latitude <= 90 and -180 <= longitude <= 180:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error validating location: {str(e)}")
        return False
# -----------------------------------------
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


@app.route('/verify-token', methods=['POST'])
def verify_token():
    data = request.get_json()
    id_token = data.get('idToken')

    if not id_token:
        return jsonify({"error": "ID token missing"}), 400

    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        return jsonify({"message": "Token verified", "uid": uid}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/')
def home():
    return "Firebase Auth Flask Backend is running."

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"message": "Merhaba AWS!"})

#KULLANICI İŞLEMLERİ
@app.route('/profile', methods=['PUT'])
def update_profile():
    data = request.get_json()
    email = data.get('email')
    
    if not email or not get_user(email):
        return jsonify({"error": "Geçersiz kullanıcı"}), 400
    
    ref = db.reference(f'/users/{email}')
    ref.update(data)
    return jsonify({"status": "success"}), 200

# @app.route('/profile/location', methods=['PUT'])
# def update_default_location():
#     try:
#         data = request.get_json()
#         new_location = data.get('location')
        
#         if not validate_location(new_location):
#             return jsonify({"error": "Geçersiz konum"}), 400
            
#         id_token=data.get('idToken')
#         decoded_token = auth.verify_id_token(id_token)
#         user_mail = decoded_token.get('email')

#         # user_mail = idToken.user['email']
#         ref = db.reference(f'/users/{user_mail}/location')
#         ref.set(new_location)
        
#         return jsonify({"status": "Konum güncellendi"}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#KULLANICI İŞLEMLERİ END
# ----------------------------------------------------------
@app.route('/profile/location', methods=['PUT'])
def update_default_location():
    try:
        # Step 1: Get data from the request
        data = request.get_json()
        new_location = data.get('location')

        if not new_location:
            return jsonify({"error": "Location is required"}), 400
        
        # Step 2: Validate the location format
        if not validate_location(new_location):
            return jsonify({"error": "Geçersiz konum"}), 400

        # Step 3: Get idToken from the request
        id_token = data.get('idToken')
        if not id_token:
            return jsonify({"error": "idToken is required"}), 400

        # Step 4: Verify the Firebase token and get the UID
        try:
            decoded_token = auth.verify_id_token(id_token)
            user_uid = decoded_token.get('uid')
            print(f"Decoded Token: {decoded_token}")  # Debugging: print the decoded token
            if not user_uid:
                return jsonify({"error": "UID not found in token"}), 400
        except Exception as e:
            print(f"Error verifying token: {str(e)}")  # Log if token verification fails
            return jsonify({"error": "Token verification failed"}), 400

        # Step 5: Construct Firebase Realtime Database reference using UID
        try:
            ref = db.reference(f'/users/{user_uid}/location')
            print(f"Firebase Reference Path: /users/{user_uid}/location")  # Debugging: print the reference path
            ref.set(new_location)
        except Exception as e:
            print(f"Error saving to Firebase: {str(e)}")  # Log if saving to Firebase fails
            return jsonify({"error": "Failed to save location"}), 500

        # Step 6: Return success response
        return jsonify({"status": "Konum güncellendi"}), 200

    except Exception as e:
        print(f"General error occurred: {str(e)}")  # Log general errors
        return jsonify({"error": str(e)}), 500

# ------------------------------------------------------------------
#WEATHER.PY ENDPOINTS
@app.route('/weather', methods=['GET'])
def get_weather_endpoint():
    """Hem varsayılan konumu hem de parametreli sorguyu destekler"""
    try:
        # 1. Kimlik Doğrulama
        id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
        decoded_token = auth.verify_id_token(id_token)
        user_email = decoded_token['email']
        
        # 2. Konum Parametresini Al
        requested_location = request.args.get('location')
        
        # 3. Konum Belirleme
        if requested_location:
            location = requested_location
            source = "parametre"
        else:
            # Firebase'den varsayılan konumu çek
            user_ref = db.reference(f'/users/{user_email}')
            user_data = user_ref.get()
            
            location = user_data.get('location', 'İstanbul')  # Fallback
            source = "varsayılan"
        
        # 4. Hava Durumu Verisini Çek
        weather_data = get_weather(location)
        if not weather_data:
            return jsonify({"error": "Hava durumu alınamadı"}), 500
            
        # 5. Yanıtı Hazırla
        return jsonify({
            "requested_by": user_email,
            "location": location,
            "source": source,
            "data": weather_data
        }), 200
        
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Geçersiz token"}), 401
    except auth.ExpiredIdTokenError:
        return jsonify({"error": "Token süresi dolmuş"}),

@app.route('/weather/weekly', methods=['GET'])
def weekly_weather():
    """7 günlük hava tahmini (varsayılan konum veya parametre ile)"""
    try:
        # 1. Kimlik Doğrulama
        id_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
        decoded_token = auth.verify_id_token(id_token)
        user_email = decoded_token['email']

        # 2. Konum Belirleme
        requested_location = request.args.get('location')
        user_ref = db.reference(f'/users/{user_email}')
        user_data = user_ref.get()
        
        location = requested_location or user_data.get('location', 'İstanbul')

        # 3. Haftalık Veriyi Çek
        api_key = os.getenv("VISUAL_CROSSING_API_KEY")
        response = requests.get(
            f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/next7days",
            params={
                "unitGroup": "metric",
                "include": "days",
                "key": api_key,
                "contentType": "json"
            },
            timeout=15
        )
        response.raise_for_status()
        
        # 4. Veriyi Formatla
        weekly_data = []
        for day in response.json().get('days', []):
            weekly_data.append({
                "date": day['datetime'],
                "temp_max": day['tempmax'],
                "temp_min": day['tempmin'],
                "precip_prob": day['precipprob'],
                "conditions": day['conditions'],
                "sunrise": day['sunrise'],
                "sunset": day['sunset']
            })

        return jsonify({
            "location": location,
            "forecast_days": len(weekly_data),
            "source": "parametre" if requested_location else "varsayılan",
            "data": weekly_data
        }), 200

    except requests.exceptions.RequestException as e:
        logger.error(f"Haftalık API hatası: {str(e)}")
        return jsonify({"error": "Hava durumu servisine ulaşılamıyor"}), 503
    except auth.InvalidIdTokenError:
        return jsonify({"error": "Geçersiz token"}), 401
    except Exception as e:
        logger.error(f"Haftalık tahmin hatası: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/weather/alerts/<user_id>', methods=['GET'])
def weather_alerts(user_id: str):
    """Kullanıcı için aktif meteorolojik uyarılar"""
    try:
        location = get_location(user_id)
        current_data = get_weather(location)
        
        # Basit geçmiş veri simülasyonu (gerçekte DB'den alınmalı)
        previous_data = {
            "current": {
                "temp": current_data['current']['temp'] + 5,  # Test için +5°C fark
                "precip": 0,
                "wind_speed": 20
            }
        }
        
        alerts = check_sudden_change(previous_data, current_data)
        
        return jsonify({
            "location": location,
            "alerts": alerts if alerts else "No active alerts",
            "last_updated": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Alert hatası: {str(e)}")
        return jsonify({"error": "Uyarılar getirilemedi"}), 500
#WEATHER.PY ENDPOINTS END    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)