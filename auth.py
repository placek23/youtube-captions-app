import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username, password_hash):
        self.id = username
        self.username = username
        self.password_hash = password_hash

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# In-memory user store - credentials loaded from environment variables
_USERS = None

def _initialize_users():
    """Initialize users from environment variables (lazy loading)."""
    global _USERS
    if _USERS is None:
        admin_username = os.environ.get('ADMIN_USERNAME')
        admin_password = os.environ.get('ADMIN_PASSWORD')

        if not admin_username or not admin_password:
            raise ValueError(
                "ADMIN_USERNAME and ADMIN_PASSWORD environment variables must be set. "
                "Please configure them in your .env file."
            )

        _USERS = {
            admin_username: User(admin_username, generate_password_hash(admin_password))
        }
    return _USERS

def get_user(username):
    users = _initialize_users()
    return users.get(username)

def authenticate_user(username, password):
    user = get_user(username)
    if user and user.check_password(password):
        return user
    return None