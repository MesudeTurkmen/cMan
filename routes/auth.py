from firebase_admin import auth
from flask import jsonify

def register_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        return jsonify({"uid": user.uid, "message": "Kullanıcı oluşturuldu"}), 200
    except auth.EmailAlreadyExistsError:
        return jsonify({"error": "Bu email zaten kayıtlı!"}), 400

def delete_user(uid):
    auth.delete_user(uid)
    return jsonify({"message": "Kullanıcı silindi"}), 200

#login