# server/app/__init__.py
from flask import Flask, send_from_directory, abort, session as flask_session, redirect, url_for
from flask_cors import CORS
from .config import config_by_name
from .utils.db import init_db, mongo
import os
from flask_login import LoginManager, current_user, login_required
from .models import User
from bson import ObjectId

# Import blueprints at the top level
from .routes.auth import auth_bp
from .routes.dialogue import dialogue_bp
from .routes.npcs import npcs_bp
from .routes.world_info import world_info_bp # Import it here

login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='../static', template_folder='../static')
    
    selected_config_object = config_by_name[config_name]
    app.config.from_object(selected_config_object)
    
    if not app.config.get('SECRET_KEY'):
        raise ValueError("SECRET_KEY not set in Flask application configuration!")

    init_db(app)
    CORS(app, supports_credentials=True)

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # Make sure you are querying by the correct field type for _id.
        # If you are storing _id as a string (e.g., from uuid.uuid4()):
        user_data = mongo.db.users.find_one({"_id": user_id})
        # If your _ids in the 'users' collection are actual MongoDB ObjectIds, use:
        # try:
        #     user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        # except Exception: # Handle cases where user_id might not be a valid ObjectId string
        #     user_data = None
            
        if user_data:
            return User(
                _id=str(user_data['_id']), # Ensure _id is consistently a string for Flask-Login
                email=user_data['email'],
                password_hash=user_data.get('password_hash'),
                google_id=user_data.get('google_id'),
                name=user_data.get('name'),
                picture=user_data.get('picture'),
                npc_ids=user_data.get('npc_ids', [])
            )
        return None

    # Register blueprints INSIDE create_app, after 'app' is defined
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')
    app.register_blueprint(npcs_bp, url_prefix='/api/npcs')
    app.register_blueprint(world_info_bp, url_prefix='/api/world-info') # MOVED HERE

    # --- Your Routes ---
    @app.route('/')
    def root_route():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard_page_route')) 
        return redirect(url_for('login_page_route_main'))    

    @app.route('/login', endpoint='login_page_route_main') 
    def login_page_route():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard_page_route'))
        
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'login.html')
        if not os.path.exists(target_path):
            current_app.logger.error(f"Login page not found at: {target_path}")
            abort(404)
        return send_from_directory(app.static_folder, 'login.html')
    
    @app.route('/npc-selector', endpoint='npc_selector_page_route') 
    @login_required 
    def npc_selector_page():
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'index.html') 
        if not os.path.exists(target_path):
            current_app.logger.error(f"NPC selector (index.html) not found at: {target_path}")
            abort(404)
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/scene', endpoint='scene_page_route') 
    @login_required 
    def scene_page():
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'scene.html')
        if not os.path.exists(target_path):
            current_app.logger.error(f"Scene page not found at: {target_path}")
            abort(404)
        return send_from_directory(app.static_folder, 'scene.html')
    
    @app.route('/dashboard', endpoint='dashboard_page_route') 
    @login_required 
    def dashboard_page():
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'dashboard.html')
        if not os.path.exists(target_path):
            current_app.logger.error(f"Dashboard page not found at: {target_path}")
            abort(404)
        return send_from_directory(app.static_folder, 'dashboard.html')

    @app.route('/health')
    def health_check():
        return "API is healthy!", 200

    login_manager.login_view = 'login_page_route_main' 
    login_manager.login_message_category = "info"

    return app