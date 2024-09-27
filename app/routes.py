from flask import request, jsonify
from app import app, mongo
from app.models import User
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import firebase_admin
import os
from firebase_admin import credentials, messaging, auth
from datetime import datetime
from bson.objectid import ObjectId


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
    firebase_id_token = data.get('firebase_id_token')

    if not firebase_id_token:
        return jsonify({'message': 'Error - Firebase ID token is missing'}), 400

    try:
        # Verify Firebase ID token
        decoded_token = auth.verify_id_token(firebase_id_token)
        user_uid = decoded_token['uid']
        email = decoded_token['email']

        # Check if user already exists in MongoDB
        user = mongo.db.users.find_one({"uid": user_uid})

        if user:
            return jsonify({"success": False, "message": "User already registered"}), 400

        # If user does not exist, add user to MongoDB
        # TODO: phone number and address, created and updated at
        new_user = {
            "firebase_uid": user_uid,
            "email": email,
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'role': data['role'],
            "email_verified": decoded_token.get('email_verified', False),
        }
        mongo.db.users.insert_one(new_user)

        return jsonify({'message': 'User registered successfully. Please check your e-mail to verify your accouont.'}), 200
    except Exception as e:
        return jsonify({'message': f'error: {str(e)}'}), 400

# Route to verify if email has been verified
""" @app.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.json
    uid = data.get('uid')

    # Fetch user from Firebase and check if email is verified
    try:
        user = firebase_admin.auth.get_user(uid)
        if user.email_verified:
            # Update MongoDB user entry as verified
            mongo.db.users.update_one({'firebase_uid': uid}, {'$set': {'verified': True}})
            return jsonify({'message': 'Email verified successfully'}), 200
        else:
            return jsonify({'error': 'Email not verified yet'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400 """

# Route for password reset (send password reset email)
@app.route('/password-reset', methods=['POST'])
def password_reset():
    data = request.json
    email = data.get('email')

    try:
        # Send password reset email via Firebase
        auth.generate_password_reset_link(email)
        return jsonify({'message': 'Password reset email sent'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    firebase_id_token = request.json

    try:
        # Verify the ID token from Firebase
        decoded_token = auth.verify_id_token(firebase_id_token)
        firebase_uid = decoded_token['uid']
        email_verified = decoded_token.get('email_verified', False)
        print(f'Email verified:  {email_verified}')

        # Create a JWT token for the session
        token = create_access_token(identity=firebase_uid)
        
        # Return the JWT token to the client along with additional information
        user = mongo.db.users.find_one({"firebase_uid": firebase_uid})
        return jsonify({'message': 'User logged in successfully', 'token': token, 'user':
                        {'id': str(user['_id']), 'email': user['email'], 'first_name': user['first_name'], 'last_name': user['last_name'], 'role': user['role']}
                        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
    fcm_token = data['fcm_token']

    current_user_firebase_id = get_jwt_identity()
    
    if fcm_token:
        mongo.db.users.update_one({"firebase_uid": current_user_firebase_id}, {"$set": {"fcm_token": fcm_token}})
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
    
@app.route('/user/<user_id>/events', methods=['GET'])
def get_events(user_id):
    # TODO: filter events based on date
    # current_date = datetime.now().isoformat() ... "date": {"$gte": current_date}
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)}, {"_id": 1, "role": 1})
    if not user:
        jsonify({"message": "No user found."}), 400

    children_events = []
    if user["role"] == "parent" or user["role"] == "admin":
        # find the parent and the corresponding children
        parent = mongo.db.parents.find_one({"user_id": ObjectId(user_id)}, {"_id": 1, "children": 1})
        children_ids = parent["children"]
        # find the groups of the children
        children_cursor = mongo.db.children.find({"_id": {"$in": children_ids}}, {"_id": 1, "first_name": 1, "classroom": 1})
        children_list = list(children_cursor)
        group_ids = list(child['classroom'].replace("Group ", "") for child in children_list)

        for i in range(len(group_ids)):
            # get all events for that group
            events = list(mongo.db.events.find({"classroom": group_ids[i]},
                                    {"_id": 1, "classroom": 1, "date": 1, "event_type": 1, "max_children_allowed": 1, "children_staying_home": 1}))
            # string conversion
            for event in events:
                event["_id"] = str(event["_id"])
                event["children_staying_home"] = [str(c) for c in event["children_staying_home"]]
            
            # add events for child and classroom
            children_events.append(
                {
                    "child_id": str(children_list[i]["_id"]),
                    "child_name": children_list[i]["first_name"],
                    "classroom": group_ids[i],
                    "events": events
                }
            )
    # TODO: move to own endpoint for teachers
    elif user["role"] == "teacher":
        teacher = mongo.db.teachers.find_one({"user_id": ObjectId(user_id)}, {"_id": 1, "assigned_classrooms": 1})
        group_ids = [group.replace("Group ", "") for group in teacher["assigned_classrooms"]]
        for i in range(len(group_ids)):
            # get all events for the group
            events = list(mongo.db.events.find({"classroom": group_ids[i]},
                                    {"_id": 1, "classroom": 1, "date": 1, "event_type": 1, "max_children_allowed": 1, "children_staying_home": 1}))
            # string conversion
            for event in events:
                event["_id"] = str(event["_id"])
                event["children_staying_home"] = [str(c) for c in event["children_staying_home"]]

            # add events to list without a child name
            children_events.append(
                {
                    "child_id": None,
                    "child_name": None,
                    "classroom": group_ids[i],
                    "events": events
                }
            )
    else:
        jsonify({"message": "Unauthorized - Only parents and teachers can retrive events."}), 403

    return jsonify(children_events), 200


@app.route('/events/<event_id>/feedback', methods=['POST'])
def post_event_feedback(event_id):
    data = request.get_json()
    child_id = data['child_id']

    # check if child exists
    child = mongo.db.children.find_one({"_id": ObjectId(child_id)}, {"_id": 1})
    if not child:
        jsonify({"message": "Child does not exist in database."}), 400
    
    # check if child has already submitted feedback to stay home
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    children_staying_home = event.get('children_staying_home', [])
    if child["_id"] in children_staying_home:
        jsonify({"message": "Feedback for child already available."}), 400
    
    mongo.db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$addToSet": {"children_staying_home": ObjectId(child_id)}}
    )

    # Also update the child's event_feedback field
    mongo.db.children.update_one(
        {"_id": ObjectId(child_id)},
        {"$addToSet": {"event_feedback": ObjectId(event_id)}}
    )
    
    return jsonify({"message": "Feedback recorded successfully"}), 200

@app.route('/events/<event_id>/feedback/<child_id>', methods=['GET'])
def get_feedback(event_id, child_id):
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    child = mongo.db.children.find_one({"_id": ObjectId(child_id)}, {"_id": 1})["_id"]
    # Find out if the child is staying home
    children_staying_home = event.get('children_staying_home', [])
    if child in children_staying_home:
        return jsonify({"staying_home": True}), 200
    else:
        return jsonify({"staying_home": False}), 200

# POST: Withdraw feedback
@app.route('/events/<event_id>/feedback/<child_id>/withdraw', methods=['POST'])
def withdraw_feedback(event_id, child_id):
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    child = mongo.db.children.find_one({"_id": ObjectId(child_id)}, {"_id": 1, "event_feedback": 1})
    if event and child["_id"]:
        children_staying_home = event.get('children_staying_home', [])
        print(children_staying_home)
        if child["_id"] in children_staying_home:
            # update event
            children_staying_home.remove(child["_id"])
            mongo.db.events.update_one({"_id": ObjectId(event_id)}, {"$set": {"children_staying_home": children_staying_home}})
            # update child feedback
            event_feedback = child["event_feedback"]
            event_feedback.remove(event["_id"])
            mongo.db.children.update_one({"_id": ObjectId(child_id)}, {"$set": {"event_feedback": event_feedback}})
            return jsonify({"message": "Feedback withdrawn"}), 200
    return jsonify({"message": "No feedback found to withdraw"}), 400