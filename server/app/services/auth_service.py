# app/services/auth_service.py
from flask import current_app
# from flask_bcrypt import Bcrypt # Using direct bcrypt as per previous setup
import bcrypt # ENSURE THIS IMPORT IS PRESENT
from ..utils.db import mongo
from ..models import User # Assuming your User model is defined
import uuid
from datetime import datetime

def register_user_s(email, password):
    users_collection = mongo.db.users
    existing_user = users_collection.find_one({"email": email})
    if existing_user:
        return None, "User with this email already exists"

    # Using direct bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()) # This line should now work

    new_user_data = {
        "_id": str(uuid.uuid4()), 
        "email": email,
        "password_hash": hashed_password.decode('utf-8'),
        "created_at": datetime.utcnow(),
        "google_id": None,
        "name": None, # You might want to add a name field to your registration form
        "picture": None,
        "npc_ids": [] 
    }
    result = users_collection.insert_one(new_user_data)
    created_user = users_collection.find_one({"_id": new_user_data["_id"]})
    if created_user:
        del created_user["password_hash"] 
    return created_user, None

def login_user_s(email, password):
    users_collection = mongo.db.users
    user_data = users_collection.find_one({"email": email})
    if not user_data or not user_data.get('password_hash'): # Check if password_hash exists
        return None, "Invalid email or password"

    if bcrypt.checkpw(password.encode('utf-8'), user_data['password_hash'].encode('utf-8')):
        user_data_safe = {k: v for k, v in user_data.items() if k != "password_hash"}
        return user_data_safe, None
    else:
        return None, "Invalid email or password"

def get_or_create_google_user(user_info):
    users_collection = mongo.db.users
    user_data = users_collection.find_one({"google_id": user_info.get("sub")}) 
    if user_data:
        user_data_safe = {k: v for k, v in user_data.items() if k != "password_hash"}
        return user_data_safe, None

    new_user_data = {
        "_id": str(uuid.uuid4()),
        "email": user_info.get("email"),
        "password_hash": None, 
        "google_id": user_info.get("sub"),
        "name": user_info.get("name"),
        "picture": user_info.get("picture"),
        "created_at": datetime.utcnow(),
        "npc_ids": []
    }
    users_collection.insert_one(new_user_data)
    # Return a safe version without the (non-existent) password hash
    del new_user_data["password_hash"] 
    return new_user_data, None