import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    if not FLASK_SECRET_KEY:
        raise Exception("FLASK_SECRET_KEY not set in environment variables")
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'fallback_secret_key')
    if not JWT_SECRET_KEY:
        raise Exception("JWT_SECRET_KEY not set in environment variables")
    MONGO_URI = os.getenv('MONGO_URI') or 'mongodb://localhost:27017/mydb'
    
    # Retrieve admin credentials
    admin_username = os.getenv('ADMIN_USERNAME')
    admin_password = os.getenv('ADMIN_PASSWORD')
