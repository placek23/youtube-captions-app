from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username, password_hash):
        self.id = username
        self.username = username
        self.password_hash = password_hash
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# In-memory user store with a strong admin user
USERS = {
    'admin_yt2024': User('admin_yt2024', generate_password_hash('SecureYT!Pass#2024$Admin'))
}

def get_user(username):
    return USERS.get(username)

def authenticate_user(username, password):
    user = get_user(username)
    if user and user.check_password(password):
        return user
    return None