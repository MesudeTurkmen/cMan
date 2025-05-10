# app.py (Ana Dosya)
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from routes.auth import *
from routes.weather import *
import firebase_admin
from firebase_admin import db
from dotenv import load_dotenv
from firebase_config import *

load_dotenv()
# Zamanlayıcı
scheduler = BackgroundScheduler()

def send_daily_notifications():
    users = db.reference('/users').get()
    for user_id, user_data in users.items():
        city = user_data.get('city', 'Istanbul')
        weather_data = get_weather(city, "your_openweather_api_key")
        if weather_data:
            message = f"{city} hava durumu: {weather_data['durum']}, {weather_data['sıcaklık']}°C"
            print(f"Bildirim gönderildi: {message}")
            # Push bildirim için: send_push_notification(user_id, message)

scheduler.add_job(send_daily_notifications, 'cron', hour=8)
scheduler.start()

app = Flask(__name__)

# Hava durumu endpoint'leri
app.add_url_rule('/weather', 'get_current_weather', get_current_weather, methods=['GET'])
app.add_url_rule('/set_city', 'set_user_city', set_user_city, methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True)