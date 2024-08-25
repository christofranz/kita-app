from flask import request, jsonify
from app import app, mongo
from app.models import User
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import firebase_admin
import os
from firebase_admin import credentials, messaging


SECRET_KEY = app.config['SECRET_KEY']
jwt = JWTManager(app)

# Initialize Firebase Admin SDK
firebase_credentials_json = os.getenv('FIREBASE_CREDENTIALS_JSON')
if not firebase_credentials_json:
    raise Exception("Path to firebase credentials json not set in environment variables")
cred = credentials.Certificate(firebase_credentials_json)  # Path to Firebase service account key
firebase_admin.initialize_app(cred)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    if mongo.db.users.find_one({'username': username}):
        return jsonify({'message': 'User already exists'}), 400
    
    # use class User to hash password
    user = User(username, password)
    mongo.db.users.insert_one({'username': user.username, 'password': user.password, 'role': user.role})
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    
    user = mongo.db.users.find_one({'username': username})
    if not user or not User.verify_password(user['password'], password):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = create_access_token(identity={'username': username, 'role': user['role']})
    return jsonify({'message': 'User logged in successfully', 'token': token, "role": user["role"]})

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/set_role', methods=['POST'])
@jwt_required()
def set_role():

    current_user = get_jwt_identity()
    if current_user['role'] != 'admin':
        return jsonify({"message": "Unauthorized - Admins only!"}), 403

    data = request.get_json()
    target_username = data['target_username']
    new_role = data['new_role']

    mongo.db.users.update_one({"username": target_username}, {"$set": {"role": new_role}})
    return jsonify({"message": "Role updated successfully"})
    
@app.route('/register_fcm_token', methods=['POST'])
@jwt_required()
def register_fcm_token():
    data = request.get_json()
    print(data)
    fcm_token = data['fcm_token']

    current_user = get_jwt_identity()
    print(current_user)
    
    if fcm_token:
        mongo.db.users.update_one({"username": current_user['username']}, {"$set": {"fcm_token": fcm_token}})
        return jsonify({"message": "Token registered successfully"}), 200
    else:
        return jsonify({"error": "Token not provided"}), 400

@app.route('/send_notification', methods=['POST'])
def send_notification():
    try:
        data = request.get_json()
        token = data.get('token')
        title = data.get('title')
        body = data.get('body')

        # Create a message to send to the device
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )

        # Send the message
        response = messaging.send(message)
        return jsonify({'success': True, 'response': response}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500