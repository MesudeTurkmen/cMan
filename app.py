from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, auth, firestore
from firebase_admin.exceptions import FirebaseError
from dotenv import load_dotenv
import os

# Firebase ve Flask Başlatma
load_dotenv()
cred = credentials.Certificate("cman-smartasst-firebase-adminsdk-fbsvc-0f0ef0dc8e.json")  # Firebase servis anahtarınızın yolu
firebase_admin.initialize_app(cred)
db = firestore.client()  # Firestore için

app = Flask(__name__)

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # 1. Firebase Authentication'da kullanıcı oluştur
        user = auth.create_user(email=email, password=password)
        
        # 2. Firestore'a ekstra bilgileri kaydet
        db.collection('users').document(user.uid).set({
            'email': email,
            'created_at': firestore.SERVER_TIMESTAMP
        })
        
        return jsonify({
            'message': 'Kayıt başarılı!',
            'uid': user.uid,
            'email': user.email
        }), 200

    except FirebaseError as e:
        return jsonify({'error': f'Firebase hatası: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Beklenmeyen hata: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # 1. Kullanıcıyı email ile bul
        user = auth.get_user_by_email(email)
        
        # 2. Şifreyi doğrula (Firebase Authentication ile)
        # Not: Firebase Admin SDK direkt şifre doğrulamaz, 
        # bu kısım için Client SDK kullanmanız veya özel bir yöntem gerekir.
        # Bu örnekte basitçe kullanıcı varlığını kontrol ediyoruz.
        
        return jsonify({
            'message': 'Giriş başarılı',
            'uid': user.uid,
            'email': user.email
        }), 200

    except auth.UserNotFoundError:
        return jsonify({'error': 'Kullanıcı bulunamadı'}), 404
    except FirebaseError as e:
        return jsonify({'error': f'Firebase hatası: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': f'Beklenmeyen hata: {str(e)}'}), 500

if __name__ == '__main__':  
    app.run(debug=True)