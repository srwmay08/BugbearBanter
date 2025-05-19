# server/app/__init__.py
from flask import Flask, send_from_directory, abort, session as flask_session
from flask_cors import CORS
from .config import config_by_name
from .utils.db import init_db, mongo # Ensure mongo is importable
import os
from flask_login import LoginManager # Add this
from .models import User # Add this
from bson import ObjectId # For loading user by ID

login_manager = LoginManager() # Add this

def create_app(config_name='default'):
    # ... (existing code) ...
    app = Flask(__name__, static_folder='../static', template_folder='../static') # Ensure template_folder is set if login.html is there

    selected_config_object = config_by_name[config_name]
    app.config.from_object(selected_config_object)

    # Critical: SECRET_KEY must be set for Flask-Login sessions
    if not app.config.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY not set in Flask application configuration!")

    init_db(app)
    CORS(app, supports_credentials=True) # supports_credentials=True for session cookies

    login_manager.init_app(app) # Add this
    login_manager.login_view = 'auth.login_route' # Route name for login page (adjust if needed)

    @login_manager.user_loader # Add this
    def load_user(user_id):
        # MongoDB stores _id as ObjectId, so convert if necessary
        # Or if you store user_id as string, query directly
        user_data = mongo.db.users.find_one({"_id": user_id}) # Assuming you use string UUIDs for _id
        # user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)}) # If using MongoDB's ObjectId
        if user_data:
            return User(
                _id=str(user_data['_id']),
                email=user_data['email'],
                password_hash=user_data.get('password_hash'),
                google_id=user_data.get('google_id'),
                name=user_data.get('name'),
                picture=user_data.get('picture'),
                npc_ids=user_data.get('npc_ids', [])
            )
        return None

    from .routes.auth import auth_bp # auth_bp should now use Flask-Login
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .routes.dialogue import dialogue_bp
    app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')

    from .routes.npcs import npcs_bp # npcs_bp will need current_user
    app.register_blueprint(npcs_bp, url_prefix='/api/npcs')

    # New route for the login page
    @app.route('/login')
    def login_page_route():
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'login.html')
        if not os.path.exists(target_path):
            print(f"Login page not found at: {target_path}")
            abort(404)
        return send_from_directory(app.static_folder, 'login.html')

    # Existing routes
    @app.route('/')
    def index_page():
        # This might become your user dashboard or redirect to login if not authenticated
        # For now, keep it as the NPC selection, but it will need user context later
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'index.html') # This is currently npc selection
        if not os.path.exists(target_path):
            abort(404)
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/scene')
    # @login_required # Add this later when you want to protect this page
    def scene_page():
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'scene.html')
        if not os.path.exists(target_path):
            abort(404)
        return send_from_directory(app.static_folder, 'scene.html')

    @app.route('/dashboard') # Example route for user dashboard
    # @login_required
    def dashboard_page():
         absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
         target_path = os.path.join(absolute_static_folder, 'dashboard.html')
         if not os.path.exists(target_path):
             print(f"Dashboard page not found at: {target_path}")
             abort(404)
         return send_from_directory(app.static_folder, 'dashboard.html')


    @app.route('/health')
    def health_check():
        return "API is healthy!", 200

    return app