import logging
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

# Initialize logger
# Configure logging
logging.basicConfig(level=logging.ERROR,  # Set to INFO or WARNING in production
                    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__name__)

from app import routes
