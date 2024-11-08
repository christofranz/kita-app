from flask import request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from app import app, mongo, logger
from app.models import User
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import firebase_admin
import os
from firebase_admin import credentials, messaging, auth
from datetime import datetime
from bson.objectid import ObjectId
from app.schemas.event_schema import EventFeedbackSchema
from app.schemas.object_schema import ObjectIdSchema
from app.schemas.user_schema import LoginSchema, UserSchema, PasswordResetSchema
from app.schemas.role_schema import SetRoleSchema
from app.schemas.firebase_schema import FcmTokenSchema, FcmMessageSchema
from marshmallow import ValidationError

# Initialize CORS with default settings (allowing all origins)
CORS(app)

# Initialize the Limiter
limiter = Limiter(
    key_func=get_remote_address,  # Use the client's IP address as the limiter key
    app=app,
    default_limits=["100 per hour", "200 per day"]  # Default: 100 requests per hour for all routes
)

# Global error handler for rate limit exceeded
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="rate limit exceeded", message=str(e.description)), 429

SECRET_KEY = app.config['FLASK_SECRET_KEY']
jwt = JWTManager(app)

# Initialize Firebase Admin SDK
cred = credentials.Certificate(app.config['FIREBASE_CREDENTIALS_JSON'])  
firebase_admin.initialize_app(cred)


@app.route('/register', methods=['POST'])
def register():
    user_schema = UserSchema()
    try:
        # Parses and validates JSON data
        data = user_schema.load(request.json)
    except ValidationError as err:
        # Log details of validation error
        logger.warning(f"Validation error during registration: {err.messages}")
        # Returns error with minimal details
        return jsonify({"message": f'Error - Invalid input.'}), 400
    
    firebase_id_token = data.get('firebase_id_token')
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

# Route for password reset (disable old tokens)
@app.route('/reset_password', methods=['POST'])
def password_reset():
    password_reset_schema = PasswordResetSchema()
    try:
        # Parses and validates JSON data
        email = password_reset_schema.load(request.json)['email']
    except ValidationError as err:
        # Log details of validation error
        logger.warning(f"Validation error during password reset: {err.messages}")
        # Returns error with minimal detail
        return jsonify({"message": f'Error - Invalid input.'}), 400

    try:
        # Check if user exists in db
        user = mongo.db.users.query.filter_by(email=email).first()
        if not user:
            logger.warning(f"Password reset requested for non-existent email.")
            # Do not reveal that the email does not exist
            return jsonify({'message': 'If an account with that email exists, a password reset email will be sent.'}), 200

        # Proceed with password reset process
        # Get the user by email
        user = auth.get_user_by_email(email)

        # Revoke all refresh tokens for the user (disables old tokens)
        auth.revoke_refresh_tokens(user.uid)
        logger.info(f"Password reset requested for email.")
        return jsonify({'message': 'Password reset email sent'}), 200
    except Exception as e:
        logger.error(f"Internal server error during password reset request: {str(e)}")
        return jsonify({'message': f'Error: Internal server error.'}), 500

@app.route('/login', methods=['POST'])
def login():
    login_schema = LoginSchema()
    try:
        # Parses and validates JSON data
        firebase_id_token = login_schema.load(request.json)['firebase_id_token']
    except ValidationError as err:
        # Log details of validation error
        logger.warning(f"Validation error during login: {err.messages}")
        # Returns error with minimal details
        return jsonify({"message": f'Error - Invalid input.'}), 400

    try:
        # Verify the ID token from Firebase
        decoded_token = auth.verify_id_token(firebase_id_token)
        firebase_uid = decoded_token['uid']
        email_verified = decoded_token.get('email_verified', False)
        if not email_verified:
            # Return error if email not verified
            return jsonify({'message:': 'Error - Email not verified'}), 401

        # Create a JWT token for the session
        token = create_access_token(identity=firebase_uid)
        
        # Return the JWT token to the client along with additional information
        user = mongo.db.users.find_one({"firebase_uid": firebase_uid})
        logger.info(f"User logged in: UID: {firebase_uid}")
        return jsonify({'message': 'User logged in successfully', 'token': token, 'user':
                        {'id': str(user['_id']), 'email': user['email'], 'first_name': user['first_name'], 'last_name': user['last_name'], 'role': user['role']}
                        }), 200
    except auth.InvalidIdTokenError:
        logger.warning("Invalid ID token provided during login.")
        return jsonify({'message': 'Error - Invalid token.'}), 401
    except Exception as e:
        # Log internal server error
        logger.error(f"Internal server error during login: {str(e)}")
        return jsonify({'message': 'Error - Internal server error.'}), 500

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/set_role', methods=['POST'])
@jwt_required()
def set_role():
    set_role_schema = SetRoleSchema()
    try:
        # Parses and validates JSON data
        data = set_role_schema.load(request.json)
    except ValidationError as err:
        # Log details of validation error
        logger.warning(f"Validation error during set_role: {err.messages}")
        # Returns error with minimal details
        return jsonify({"message": f'Error - Invalid input.'}), 400
    
    # verify if the admin is setting the role
    current_user_firebase_id = get_jwt_identity()
    current_role = mongo.db.users.find_one({"firebase_uid": current_user_firebase_id}, {'role': 1})['role']
    if current_role != 'admin':
        return jsonify({"message": "Unauthorized - Admins only!"}), 403

    # update role in db
    target_username = data['target_username']
    new_role = data['new_role']
    mongo.db.users.update_one({"username": target_username}, {"$set": {"role": new_role}})
    return jsonify({"message": "Role updated successfully"})
    
@app.route('/register_fcm_token', methods=['POST'])
@jwt_required()
def register_fcm_token():
    fcm_token_schema = FcmTokenSchema()
    try:
        # Parses and validates JSON data
        data = fcm_token_schema.load(request.json)
    except ValidationError as err:
        # Log details of validation error
        logger.warning(f"Validation error during registration of fcm token: {err.messages}")
        # Returns error with minimal details
        return jsonify({"message": f'Error - Invalid input.'}), 400
    
    # update token in db
    fcm_token = data['fcm_token']
    current_user_firebase_id = get_jwt_identity()
    mongo.db.users.update_one({"firebase_uid": current_user_firebase_id}, {"$set": {"fcm_token": fcm_token}})
    return jsonify({"message": "Token registered successfully"}), 200
 

@app.route('/send_notification', methods=['POST'])
def send_notification():
    notification_schema = FcmMessageSchema()
    try:
        # Parses and validates JSON data
        data = notification_schema.load(request.json)
    except ValidationError as err:
        # Log details of validation error
        logger.warning(f"Validation error during registration: {err.messages}")
        # Returns validation errors if the input is invalid
        return jsonify({"message": f'Error - {err.messages}'}), 400
    
    try:
        fcm_token = data['fcm_token']
        title = data['title']
        body = data['body']

        # Create a message to send to the device
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=fcm_token,
        )

        # Send the message
        response = messaging.send(message)
        return jsonify({'success': True, 'response': response}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/user/<user_id>/events', methods=['GET'])
@jwt_required()
def get_events(user_id):
    user_id_schema = ObjectIdSchema()
    try:
        # Parses and validates JSON data
        user_id = user_id_schema.load(user_id)
    except ValidationError as err:
        # Log details of validation error
        logger.warning(f"Validation error during getting events: {err.messages}")
        # Returns error with minimal details
        return jsonify({"message": "Error - Invalid input."}), 400

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)}, {"_id": 1, "role": 1, "firebase_uid": 1})

    # if no user with that user_id exists
    if not user:
        logger.warning(f"Events requested for not existing user_id: {user_id}")
        jsonify({"message": "No user found."}), 400

    # verify if user_id matches to logged in user
    current_user_firebase_id = get_jwt_identity()
    if user["firebase_uid"] != current_user_firebase_id:
        logger.warning(f"User_id mismatch for getting events. Given user_id does not fit to logged in user_id.")
        jsonify({"message": "Unauthorized access"}), 403

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
        logger.warning("Role of the user requesting events is not allowed.")
        jsonify({"message": "Unauthorized access."}), 403
    
    logger.info(f"Events retrieved for user_id.")
    return jsonify(children_events), 200


@app.route('/events/<event_id>/feedback', methods=['POST'])
def post_event_feedback(event_id):
    event_id_schema = ObjectIdSchema()
    event_feedback_schema = EventFeedbackSchema()
    try:
        # Parses and validates JSON data
        event_id = event_id_schema.load(event_id)
        data = event_feedback_schema.load(request.json)
    except ValidationError as err:
        # Log details of validation error
        logger.warning(f"Validation error during posting event feedback: {err.messages}")
        # Returns error with minimal details
        return jsonify({"message": f'Error - Invalid input.'}), 400    

    child_id = data['child_id']
    # check if child exists
    child = mongo.db.children.find_one({"_id": ObjectId(child_id)}, {"_id": 1})
    if not child:
        logger.warning(f"Event feedback posted for child_id {child_id} that does not exist.")
        jsonify({"message": "Error - Invalid input."}), 400
    
    # check if child has already submitted feedback to stay home
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    children_staying_home = event.get('children_staying_home', [])
    if child["_id"] in children_staying_home:
        logger.warning(f"Feedback for child_id {child_id} is already available.")
        jsonify({"message": "Error - Invalid input."}), 400
    
    mongo.db.events.update_one(
        {"_id": ObjectId(event_id)},
        {"$addToSet": {"children_staying_home": ObjectId(child_id)}}
    )

    # Also update the child's event_feedback field
    mongo.db.children.update_one(
        {"_id": ObjectId(child_id)},
        {"$addToSet": {"event_feedback": ObjectId(event_id)}}
    )
    logger.info(f"Stored event feedback for child successfully.")
    return jsonify({"message": "Feedback recorded successfully"}), 200

@app.route('/events/<event_id>/feedback/<child_id>', methods=['GET'])
def get_feedback(event_id, child_id):
    event_id_schema = ObjectIdSchema()
    child_id_schema = ObjectIdSchema()
    try:
        # Parses and validates JSON data
        event_id = event_id_schema.load(event_id)
        child_id = child_id_schema.load(child_id)
    except ValidationError as err:
        # Log details of validation error
        logger.warning(f"Validation error during getting feedback for event: {err.messages}")
        # Returns error with minimal feedback
        return jsonify({"message": f'Error - Invalid input.'}), 400
    
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    # check if event exists
    if not event:
        logger.warning(f"Requested feedback for event_id {event_id} that does not exist.")
        jsonify({"message": "Error - Invalid input."}), 400
    child = mongo.db.children.find_one({"_id": ObjectId(child_id)}, {"_id": 1})["_id"]
    # check if child exists
    if not child:
        logger.warning(f"Requested event feedback for child_id {child_id} that does not exist.")
        jsonify({"message": "Error - Invalid input."}), 400

    logger.info("Returning feedback for child if staying home.")
    # Find out if the child is staying home
    children_staying_home = event.get('children_staying_home', [])
    if child in children_staying_home:
        return jsonify({"staying_home": True}), 200
    else:
        return jsonify({"staying_home": False}), 200

@app.route('/events/<event_id>/feedback/<child_id>/withdraw', methods=['POST'])
def withdraw_feedback(event_id, child_id):
    event_id_schema = ObjectIdSchema()
    child_id_schema = ObjectIdSchema()
    try:
        # Parses and validates JSON data
        event_id = event_id_schema.load(event_id)
        child_id = child_id_schema.load(child_id)
    except ValidationError as err:
        # Log details of validation error
        logger.warning(f"Validation error during withdrawing feedback: {err.messages}")
        # Returns error with minimal details
        return jsonify({"message": f'Error - Invalid input.'}), 400
    
    event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
    # check if event exists
    if not event:
        logger.warning(f"Requested feedback for event_id {event_id} that does not exist.")
        jsonify({"message": "Error - Invalid input."}), 400
    child = mongo.db.children.find_one({"_id": ObjectId(child_id)}, {"_id": 1, "event_feedback": 1})
    # check if child exists
    if not child:
        logger.warning(f"Requested event feedback for child_id {child_id} that does not exist.")
        jsonify({"message": "Error - Invalid input."}), 400

    children_staying_home = event.get('children_staying_home', [])
    if child["_id"] in children_staying_home:
        # update event
        children_staying_home.remove(child["_id"])
        mongo.db.events.update_one({"_id": ObjectId(event_id)}, {"$set": {"children_staying_home": children_staying_home}})
        # update child feedback
        event_feedback = child["event_feedback"]
        event_feedback.remove(event["_id"])
        mongo.db.children.update_one({"_id": ObjectId(child_id)}, {"$set": {"event_feedback": event_feedback}})
        logger.info("Withdrawing child feedback for event.")
        return jsonify({"message": "Feedback withdrawn"}), 200
    else:
        logger.warning(f"Attempt to withdraw child feedback that does not exist.")
        return jsonify({"message": "Error - Invalid input."}), 400