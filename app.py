# app.py (Ana Dosya)
from flask import Flask

from routes.auth import *
from routes.weather import *

import firebase_admin
from firebase_admin import db
from dotenv import load_dotenv
from firebase_config import *

load_dotenv()

app = Flask(__name__)

if __name__ == '__main__':
    app.run(debug=True)
