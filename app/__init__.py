from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from config import Config
from datetime import timedelta

app = Flask(__name__)
app.config.from_object(Config)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
    
CORS(app)
mongo = PyMongo(app)

from app import routes
