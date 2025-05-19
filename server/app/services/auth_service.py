# app/services/auth_service.py
from flask import current_app
from flask_bcrypt import Bcrypt # Or use direct bcrypt
from ..utils.db import mongo
from ..models import User # Assuming your User model is defined
import uuid
from datetime import datetime

# Initialize bcrypt here if you use Flask-Bcrypt
# bcrypt = Bcrypt() # Can be initialized in create_app and passed around or used as current_app.extensions['bcrypt']

def register_user_s(email, password):
    users_collection = mongo.db.users
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        return None, "User with this email already exists"

    # Using direct bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    new_user_data = {
        "_id": str(uuid.uuid4()), # Or use MongoDB's ObjectId
        "email": email,
        "password_hash": hashed_password.decode('utf-8'),
        "created_at": datetime.utcnow(),
        "google_id": None,
        "npc_ids": [] # To store IDs of NPCs uploaded by this user
    }
    result = users_collection.insert_one(new_user_data)
    # Fetch the created user to return (optional, depends on your needs)
    created_user = users_collection.find_one({"_id": new_user_data["_id"]})
    if created_user:
        del created_user["password_hash"] # Don't send hash back
    return created_user, None

def login_user_s(email, password):
    users_collection = mongo.db.users
    user_data = users_collection.find_one({"email": email})
    if not user_data:
        return None, "Invalid email or password"

    if bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
        # Password matches
        # In a real app, you'd generate a session token (JWT) or use Flask-Login here
        user_obj = User(email=user_data['email'], password_hash=user_data['password_hash'], google_id=user_data.get('google_id'))
        # For now, just return the user data (excluding password hash)
        user_data_safe = {k: v for k, v in user_data.items() if k != "password_hash"}
        return user_data_safe, None
    else:
        return None, "Invalid email or password"

# Placeholder for Google Sign-In user creation/retrieval
def get_or_create_google_user(user_info):
    users_collection = mongo.db.users
    user_data = users_collection.find_one({"google_id": user_info.get("sub")}) # "sub" is Google's user ID
    if user_data:
        user_data_safe = {k: v for k, v in user_data.items() if k != "password_hash"}
        return user_data_safe, None # Existing user

    # Create new user for Google Sign-In
    new_user_data = {
        "_id": str(uuid.uuid4()),
        "email": user_info.get("email"),
        "password_hash": None, # No password for Google-only users
        "google_id": user_info.get("sub"),
        "name": user_info.get("name"),
        "picture": user_info.get("picture"),
        "created_at": datetime.utcnow(),
        "npc_ids": []
    }
    users_collection.insert_one(new_user_data)
    return new_user_data, None