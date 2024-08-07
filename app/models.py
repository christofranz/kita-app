from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, username, password, role="parent"):
        self.username = username
        self.password = generate_password_hash(password)
        self.role = role

    @staticmethod
    def verify_password(stored_password, provided_password):
        return check_password_hash(stored_password, provided_password)
