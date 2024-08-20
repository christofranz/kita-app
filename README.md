https://stackoverflow.com/questions/51417708/unable-to-install-mongodb-properly-on-ubuntu-18-04-lts um mongodb zu installieren

datenbank anzeigen mit mongo shell:
# Start the MongoDB shell
mongo

# Switch to the user_database
use mydb #use show dbs to see databases

# List all collections
show collections

# Inspect the users collection
db.users.find().pretty()


install android studio
https://developer.android.com/studio/install


secret key to replace:
import secrets

# Generate a URL-safe text string, containing 32 random bytes
secret_key = secrets.token_urlsafe(32)
print(secret_key)

Step 3: Securely Store the Secret Key
It's important to securely store the secret key, especially in a production environment. Hardcoding the secret key directly in your source code is not a best practice. Instead, consider using environment variables.

Set Environment Variable:

On Unix-based systems (Linux, macOS):

sh
Copy code
export FLASK_SECRET_KEY='your_generated_secret_key_here'
On Windows:

sh
Copy code
set FLASK_SECRET_KEY=your_generated_secret_key_here

https://stackoverflow.com/questions/51621301/android-studio-3-1-3-unresolved-reference-r-kotlin -> findviewbyid is deprecated


Android app:
Allow Self-Signed Certificates in Development
For development purposes, you can configure your OkHttpClient to trust all certificates. Note: This should only be used in a development environment.


Firebase
Own backend or firebase: https://medium.com/firebase-developers/what-is-firebase-the-complete-story-abridged-bcc730c5f2c0

# admin user
set environment variables 
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=admin_password  # Replace with a secure password

# Android
- set up xiamoi phone for usb debugging: https://medium.com/@Sammy_Hasan/developing-for-xiaomi-from-android-studio-8b4713dc7d63
- use physical device needs adaptation of connection: https://medium.com/@kennethchangla/debugging-android-how-to-connect-to-local-server-81ddcd8f3f9d -> enable port forwarding and use local host ip and not emulator ip (5000 -> localhost: 5000)
![alt text](image.png)

# TODOs
- use token from backend after login in android app and in the requests
- adapt set_role request to use token from admin and not the admin username
- android requests with bearer token authentication?
- nginx reverse proxy https
- icon sichtbar bei installation physikalisches Gerät
- login session bleibt gültig