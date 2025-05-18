# ---- server/app/routes/auth.py ----
from flask import Blueprint, request, jsonify
# from ..services.auth_service import register_user, login_user # Example import
# from ..utils.db import mongo # If you need direct db access, though services are preferred
import bcrypt # For password hashing

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint.
    Expects JSON: { "email": "...", "password": "..." }
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    email = data['email']
    password = data['password']

    # Basic validation (more robust validation should be added)
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400

    # In a real app, you'd call a service function:
    # user, error = register_user(email, password)
    # if error:
    #     return jsonify({"error": error}), 400
    # return jsonify(user.to_dict()), 201

    # --- Placeholder logic for now ---
    # Check if user already exists (example using direct mongo access)
    # from ..utils.db import mongo # Corrected import for blueprint context
    # if mongo.db.users.find_one({"email": email}):
    #     return jsonify({"error": "User with this email already exists"}), 409

    # Hash the password
    # hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # new_user_data = {
    #     "email": email,
    #     "password_hash": hashed_password.decode('utf-8'), # Store as string
    #     "created_at": datetime.datetime.utcnow()
    # }
    # result = mongo.db.users.insert_one(new_user_data)
    # created_user = mongo.db.users.find_one({"_id": result.inserted_id})
    
    # # Convert ObjectId to string for the response
    # if created_user:
    #    created_user["_id"] = str(created_user["_id"])
    #    del created_user["password_hash"] # Don't send hash back

    # return jsonify({"message": "User registered successfully", "user": created_user}), 201
    # --- End Placeholder ---
    
    return jsonify({"message": "Registration endpoint placeholder. Integrate with auth_service."}), 200


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.
    Expects JSON: { "email": "...", "password": "..." }
    """
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    # In a real app, you'd call a service function:
    # token, error = login_user(data['email'], data['password'])
    # if error:
    #     return jsonify({"error": error}), 401
    # return jsonify({"token": token}), 200
    
    return jsonify({"message": "Login endpoint placeholder. Integrate with auth_service."}), 200


# Add routes for Google login, logout, Patreon integration callback etc.
