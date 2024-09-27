import random
from config import Config
from pymongo import MongoClient
from datetime import datetime, timedelta
from faker import Faker
from werkzeug.security import generate_password_hash


# Initialize Faker for generating random data
fake = Faker()

# MongoDB connection
client = MongoClient(Config.MONGO_URI)
db = client.mydb

# Clear collections
db.users.drop()
db.children.drop()
db.parents.drop()
db.teachers.drop()
db.classrooms.drop()
db.events.drop()

# Collections
user_collection = db.users
children_collection = db.children
parents_collection = db.parents
teachers_collection = db.teachers
classrooms_collection = db.classrooms
events_collection = db.events

# Helper function to create users
def create_user(role):
    return db.users.insert_one({
        "email": fake.email(),
        "password": generate_password_hash(fake.password()),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "phone_number": fake.phone_number(),
        "address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "postal_code": fake.zipcode()
        },
        "role": role,
        "verified": True
    }).inserted_id

# Function to create parents
def create_parents(num_parents):
    parent_ids = []
    # create parent user for testing
    parent_user_id = db.users.insert_one({
        "email": "tester@web.com",
        "password": generate_password_hash("test"),
        "first_name": "Test",
        "last_name": "Debugger",
        "phone_number": fake.phone_number(),
        "address": {
                "street": fake.street_address(),
                "city": fake.city(),
                "state": fake.state(),
                "postal_code": fake.zipcode()
        },
        "role": "admin",
        "verified": True
    }).inserted_id
    parent = {
        "user_id": parent_user_id,
        "relation_to_child": random.choice(["Mother", "Father"]),
        "children": []  # Will be filled later with ObjectIds of their children
    }
    parent_id = parents_collection.insert_one(parent).inserted_id
    parent_ids.append(parent_id)
    # create remaining parents with fake values
    for _ in range(num_parents-1):
        parent_user_id = create_user("parent")
        parent = {
            "user_id": parent_user_id,
            "relation_to_child": random.choice(["Mother", "Father"]),
            "children": []  # Will be filled later with ObjectIds of their children
        }
        parent_id = parents_collection.insert_one(parent).inserted_id
        parent_ids.append(parent_id)
    return parent_ids

# Function to create children
def create_children(num_children, parent_ids):
    child_ids = []
    remaining_parent_ids = parent_ids # to ensure all parents have children
    for _ in range(num_children):
        parent_ids_child = random.sample(remaining_parent_ids, 2)
        remaining_parent_ids = list(set(remaining_parent_ids) - set(parent_ids_child))
        child = {
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "date_of_birth": fake.date_of_birth(minimum_age=3, maximum_age=5).isoformat(),
            "gender": random.choice(["Male", "Female"]),
            "enrollment_date": fake.date_this_year().isoformat(),
            "classroom": f"Group {random.choice(['A', 'B', 'C'])}",
            "medical_info": {
                "allergies": random.choices(["Peanuts", "Dairy", "None"], k=2),
                "medications": ["Inhaler"] if random.choice([True, False]) else [],
                "special_needs": random.choice(["None", "Speech Therapy", "Physical Therapy"])
            },
            "emergency_contacts": [
                {
                    "name": fake.name(),
                    "relation": "Neighbor",
                    "phone_number": fake.phone_number(),
                    "email": fake.email()
                }
            ],
            "parents": parent_ids_child,
            "activities": [],
            "event_feedback": []  # List of event IDs the child has volunteered to stay home for
        }
        child_id = children_collection.insert_one(child).inserted_id
        child_ids.append(child_id)

        # Add the child ID to each parent's children list
        for parent_id in child["parents"]:
            parents_collection.update_one({"_id": parent_id}, {"$push": {"children": child_id}})
    
    return child_ids

# Function to create teachers
def create_teachers(num_teachers):
    teacher_ids = []
    for _ in range(num_teachers):
        teacher_user_id = create_user("teacher")
        teacher = {
            "user_id": teacher_user_id,
            "assigned_classrooms": [f"Group {random.choice(['A', 'B', 'C'])}"],
            "qualifications": [
                "Bachelor's in Early Childhood Education",
                "First Aid Certification"
            ],
            "employment_date": fake.date_between(start_date='-5y', end_date='today').isoformat()
        }
        teacher_id = teachers_collection.insert_one(teacher).inserted_id
        teacher_ids.append(teacher_id)
    return teacher_ids

# Function to create classrooms
def create_classrooms(groups, teacher_ids):
    for group in groups:
        classroom = {
            "name": f"Group {group}",
            "teacher": random.choice(teacher_ids),
            "students": []
        }
        classrooms_collection.insert_one(classroom)

# Function to create events
def create_events(classroom_names, num_events=5):
    for _ in range(num_events):
        event_type = random.choice(["Classroom Closed", "Limited Attendance"])
        max_children = random.randint(5, 20) if event_type == "Limited Attendance" else 0
        
        event = {
            "classroom": random.choice(classroom_names),
            "date": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat(),
            "event_type": event_type,
            "max_children_allowed": max_children,
            "children_staying_home": []  # List of child IDs who volunteered to stay home
        }
        events_collection.insert_one(event)

# Initialize database with data
parent_ids = create_parents(num_parents=80)  # 40 children, 2 parents each, each parent a child
child_ids = create_children(num_children=40, parent_ids=parent_ids)
teacher_ids = create_teachers(num_teachers=10)
create_classrooms(groups=['A', 'B', 'C'], teacher_ids=teacher_ids)
create_events(classroom_names=['A', 'B', 'C'], num_events=10)

print("Database initialization completed successfully.")
