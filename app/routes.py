from flask import request, jsonify
from app import app, mongo
from app.models import User
import jwt
import datetime

SECRET_KEY = app.config['SECRET_KEY']

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
    
    token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, SECRET_KEY)
    return jsonify({'message': 'User logged in successfully', 'token': token, "role": user["role"]})

@app.route('/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing'}), 403
    
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        return jsonify({'message': 'Token is invalid'}), 403
    
    return jsonify({'message': 'This is a protected route', 'user': data['username']})

@app.route('/set_role', methods=['POST'])
def set_role():
    data = request.get_json()
    admin_username = data['admin_username']
    target_username = data['target_username']
    new_role = data['new_role']

    admin_user = mongo.db.users.find_one({"username": admin_username})
    if admin_user and admin_user['role'] == 'admin':
        mongo.db.users.update_one({"username": target_username}, {"$set": {"role": new_role}})
        return jsonify({"message": "Role updated successfully"})
    else:
        return jsonify({"message": "Unauthorized"}), 403
