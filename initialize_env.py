import os
import secrets
from dotenv import load_dotenv, set_key

# Load the .env file if it exists
dotenv_path = '.env'
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Generate random secret keys
def generate_secret_key():
    return secrets.token_hex(32)  # 32 bytes hex token (64 characters)

# Check if FLASK_SECRET_KEY and JWT_SECRET_KEY are already set
flask_secret_key = os.getenv('FLASK_SECRET_KEY')
jwt_secret_key = os.getenv('JWT_SECRET_KEY')

if not flask_secret_key:
    flask_secret_key = generate_secret_key()
    print(f"Generated FLASK_SECRET_KEY: {flask_secret_key}")
    set_key(dotenv_path, 'FLASK_SECRET_KEY', flask_secret_key)

if not jwt_secret_key:
    jwt_secret_key = generate_secret_key()
    print(f"Generated JWT_SECRET_KEY: {jwt_secret_key}")
    set_key(dotenv_path, 'JWT_SECRET_KEY', jwt_secret_key)

print("Keys have been successfully saved to .env file.")
