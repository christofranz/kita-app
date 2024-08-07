import os
from app import mongo
from app.models import User

# Connect to the MongoDB database
# SECRET_KEY = app.config['SECRET_KEY']

# Retrieve admin credentials from environment variables
admin_username = os.getenv('ADMIN_USERNAME')
admin_password = os.getenv('ADMIN_PASSWORD')

if not admin_username or not admin_password:
    raise Exception("Admin username or password not set in environment variables")

# Check if the admin user already exists
admin_user = mongo.db.users.find_one({"username": admin_username})

if not admin_user:
    # If admin user does not exist, create it
    admin_user = User(admin_username, admin_password, "admin")
    mongo.db.users.insert_one({"username": admin_user.username, "password": admin_user.password, "role": admin_user.role})
    print("Admin user created.")
else:
    print("Admin user already exists.")
