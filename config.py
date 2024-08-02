import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY') or 'you-will-never-guess'
    MONGO_URI = os.getenv('MONGO_URI') or 'mongodb://localhost:27017/mydb'