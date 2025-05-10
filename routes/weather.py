# routes/weather.py
import requests
from flask import jsonify, request
from firebase_admin import db
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# 1. Hava Durumu Verisi Çekme
def get_weather(city):
    api_key = os.getenv("OPENWEATHER_API_KEY")
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
        'lang': 'tr'
    }
    
    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            data = response.json()
            return {
                "temp": data['main']['temp'],
                "description": data['weather'][0]['description'],
                "humidity": data['main']['humidity'],
                "timestamp": datetime.now().isoformat()  # Veri çekme zamanı
            }
        return None
    except Exception as e:
        print("API Hatası:", str(e))
        return None


def get_time(user_id):
    """Firebase'den kullanıcının bildirim saatini çeker."""
    try:
        user_ref = db.reference(f'/users/{user_id}')
        user_data = user_ref.get()
        return user_data.get('notification_time', '08:00')  # Varsayılan 08:00
    except Exception as e:
        print("Firebase Hatası:", str(e))
        return '08:00'

# 3. Ani Hava Değişimi Uyarısı
def check_sudden_change(city, threshold=5):
    current_weather = get_weather(city)
    if not current_weather:
        return None
    
    # Önceki veriyi Firebase'den al
    prev_weather_ref = db.reference(f'/weather_history/{city}')
    prev_weather = prev_weather_ref.get()
    
    # Değişimi kontrol et
    alert = None
    if prev_weather:
        temp_change = abs(current_weather['temp'] - prev_weather['temp'])
        if temp_change > threshold:
            alert = f"⚠️ {city}'de ani sıcaklık değişimi! ({temp_change}°C)"
    
    # Yeni veriyi Firebase'e yaz
    prev_weather_ref.set(current_weather)
    return alert


def schedule_weather_alerts():
    """APScheduler ile entegre çalışacak periyodik bildirim fonksiyonu."""
    users_ref = db.reference('/users')
    users = users_ref.get()
    
    for user_id, user_data in users.items():
        city = user_data.get('city', 'Istanbul')
        alert = check_sudden_change(city)
        if alert:
            # Firebase'e bildirim kaydet (veya FCM ile gönder)
            db.reference(f'/notifications/{user_id}').push().set({
                "message": alert,
                "timestamp": datetime.now().isoformat()
            })