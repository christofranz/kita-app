import pytest
from app import app, mongo

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['MONGO_URI'] = 'mongodb://localhost:27017/test_db'
    client = app.test_client()

    with app.app_context():
        mongo.db.users.delete_many({})  # Clear the test database before each test

    yield client

def test_register(client):
    response = client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['message'] == 'User registered successfully'

def test_register_existing_user(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    response = client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['message'] == 'User already exists'
