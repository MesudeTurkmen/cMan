# routes/weather.py
import requests
from flask import jsonify, request
from firebase_admin import db
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_weather(city):
    """OpenWeatherMap One Call API ile 48 saatlik ve 7 günlük tahmin."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    
    # 1. Şehrin koordinatlarını bul (Geocoding API)
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    geo_params = {
        'q': city,
        'limit': 1,
        'appid': api_key
    }
    geo_response = requests.get(geo_url, params=geo_params)
    
    if geo_response.status_code != 200 or not geo_response.json():
        return jsonify({"error": "Şehir bulunamadı"}), 404
    
    lat = geo_response.json()[0]['lat']
    lon = geo_response.json()[0]['lon']
    
    # 2. Hava durumu tahmini (One Call API 3.0)
    weather_url = "https://api.openweathermap.org/data/3.0/onecall"
    weather_params = {
        'lat': lat,
        'lon': lon,
        'exclude': 'minutely',
        'units': 'metric',
        'lang': 'tr',
        'appid': api_key
    }
    weather_response = requests.get(weather_url, params=weather_params)
    
    if weather_response.status_code != 200:
        return jsonify({"error": "Hava durumu alınamadı"}), 500
    
    data = weather_response.json()
    
    # 3. Saatlik Tahmin (Önümüzdeki 24 saat)
    hourly_forecast = []
    for hour in data['hourly'][:24]:
        hourly_forecast.append({
            "saat": datetime.fromtimestamp(hour['dt']).strftime("%H:%M"),
            "sıcaklık": hour['temp'],
            "durum": hour['weather'][0]['description'],
            "yağış olasılığı": f"%{int(hour.get('pop', 0)*100)}",
            "yağış miktarı (mm)": hour.get('rain', {}).get('1h', 0)
        })
    
    # 4. 5 Günlük Tahmin (Günlük Max/Min)
    daily_forecast = []
    for day in data['daily'][:5]:
        daily_forecast.append({
            "tarih": datetime.fromtimestamp(day['dt']).strftime("%d.%m"),
            "max_sıcaklık": day['temp']['max'],
            "min_sıcaklık": day['temp']['min'],
            "durum": day['weather'][0]['description']
        })
    
    return jsonify({
        "şehir": city,
        "anlık": {
            "sıcaklık": data['current']['temp'],
            "hissedilen": data['current']['feels_like'],
            "nem": f"%{data['current']['humidity']}",
            "rüzgar": f"{data['current']['wind_speed']} m/s"
        },
        "saatlik_tahmin": hourly_forecast,
        "5_günlük_tahmin": daily_forecast
    }), 200

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

print(get_weather("Istanbul"))