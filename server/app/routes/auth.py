# app/routes/auth.py
from flask import Blueprint, request, jsonify, current_app, session
from ..services.auth_service import register_user_s, login_user_s, get_or_create_google_user
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User # Ensure User model is imported
import os

# For Google Sign-In backend verification
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register_route():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    email = data['email']
    password = data['password']

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400

    user_data, error = register_user_s(email, password)
    if error:
        return jsonify({"error": error}), 400 # Or 409 for conflict

    # Log the user in immediately after registration
    # Need to fetch the full User object for Flask-Login
    created_user_obj = User(
        _id=user_data['_id'], email=user_data['email'], 
        google_id=user_data.get('google_id'), name=user_data.get('name'),
        npc_ids=user_data.get('npc_ids', [])
    )
    login_user(created_user_obj) # Flask-Login function
    current_app.logger.info(f"User {email} registered and logged in.")
    return jsonify({"message": "User registered successfully", "user": user_data}), 201

@auth_bp.route('/login', methods=['POST'])
def login_route():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    email = data['email']
    password = data['password']
    user_data, error = login_user_s(email, password)

    if error:
        return jsonify({"error": error}), 401

    # Create User object for Flask-Login
    user_obj = User(
        _id=user_data['_id'], email=user_data['email'], 
        google_id=user_data.get('google_id'), name=user_data.get('name'),
        npc_ids=user_data.get('npc_ids', [])
    )
    login_user(user_obj) # Flask-Login function
    current_app.logger.info(f"User {email} logged in.")
    return jsonify({"message": "Login successful", "user": user_data}), 200

@auth_bp.route('/logout', methods=['POST'])
@login_required # Ensure user is logged in to log out
def logout_route():
    logout_user() # Flask-Login function
    return jsonify({"message": "Logout successful"}), 200

@auth_bp.route('/status', methods=['GET'])
def status_route():
    if current_user.is_authenticated:
        user_data = {
            "_id": str(current_user._id),
            "email": current_user.email,
            "name": current_user.name,
            "picture": current_user.picture,
            "google_id": current_user.google_id,
            "npc_ids": current_user.npc_ids
        }
        return jsonify({"logged_in": True, "user": user_data}), 200
    else:
        return jsonify({"logged_in": False}), 200

@auth_bp.route('/google-signin', methods=['POST'])
def google_signin_route():
    data = request.get_json()
    token = data.get('credential') # This is the ID token from Google Sign-In on frontend
    GOOGLE_CLIENT_ID = current_app.config.get('GOOGLE_CLIENT_ID')

    if not token:
        return jsonify({"error": "No token provided"}), 400
    if not GOOGLE_CLIENT_ID:
        current_app.logger.error("GOOGLE_CLIENT_ID not configured on the server.")
        return jsonify({"error": "Google Sign-In not configured on server."}), 500

    try:
        # Verify the ID token
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        # userid = idinfo['sub']
        # email = idinfo['email']
        # name = idinfo.get('name')
        # picture = idinfo.get('picture')

        user_data, error = get_or_create_google_user(idinfo)
        if error:
            return jsonify({"error": error}), 500

        user_obj = User(
            _id=user_data['_id'], email=user_data['email'],
            google_id=user_data.get('google_id'), name=user_data.get('name'),
            picture=user_data.get('picture'), npc_ids=user_data.get('npc_ids', [])
        )
        login_user(user_obj)
        current_app.logger.info(f"User {user_data['email']} logged in via Google.")
        return jsonify({"message": "Google Sign-In successful", "user": user_data}), 200

    except ValueError as e:
        # Invalid token
        current_app.logger.error(f"Google token verification failed: {e}")
        return jsonify({"error": "Invalid Google token"}), 401
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred during Google Sign-In: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500