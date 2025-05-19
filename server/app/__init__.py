# server/app/__init__.py
from flask import Flask, send_from_directory, abort, session as flask_session, redirect, url_for # Added redirect, url_for
from flask_cors import CORS
from .config import config_by_name
from .utils.db import init_db, mongo
import os
from flask_login import LoginManager, current_user, login_required # Add login_required here
from .models import User
from bson import ObjectId
from .routes.world_info import world_info_bp # Add import
from .models import User
from bson import ObjectId

app.register_blueprint(world_info_bp, url_prefix='/api/world-info') # Add registration

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
    login_manager.login_view = 'auth.login_page_route' # Corrected: This should be the *endpoint name* of your login page route
                                                    # e.g., if your @app.route('/login') is named login_page_route in auth_bp or here

    @login_manager.user_loader
    def load_user(user_id):
        user_data = mongo.db.users.find_one({"_id": user_id}) 
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

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .routes.dialogue import dialogue_bp
    app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')

    from .routes.npcs import npcs_bp
    app.register_blueprint(npcs_bp, url_prefix='/api/npcs')
    
    app.register_blueprint(world_info_bp, url_prefix='/api/world-info') # <<< ADD THIS LINE


    # --- Modified Root Route ---
    @app.route('/')
    def root_route():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard_page_route')) # Redirect to dashboard if logged in
        return redirect(url_for('login_page_route_main'))    # Redirect to login if not

    # New route for the login page (served from main app, not auth blueprint for direct access)
    @app.route('/login', endpoint='login_page_route_main') # Added endpoint name
    def login_page_route():
        # If user is already authenticated and tries to go to /login, redirect to dashboard
        if current_user.is_authenticated:
            return redirect(url_for('dashboard_page_route'))
        
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'login.html')
        if not os.path.exists(target_path):
            print(f"Login page not found at: {target_path}")
            abort(404)
        return send_from_directory(app.static_folder, 'login.html')
    
    # Renamed to avoid conflict with the general concept of "index"
    @app.route('/npc-selector', endpoint='npc_selector_page_route') # Added endpoint name
    @login_required # Protect this page
    def npc_selector_page():
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        # This serves index.html which is your NPC selector
        target_path = os.path.join(absolute_static_folder, 'index.html') 
        if not os.path.exists(target_path):
            abort(404)
        return send_from_directory(app.static_folder, 'index.html')


    @app.route('/scene', endpoint='scene_page_route') # Added endpoint name
    @login_required # Protect this page
    def scene_page():
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'scene.html')
        if not os.path.exists(target_path):
            abort(404)
        return send_from_directory(app.static_folder, 'scene.html')
    
    @app.route('/dashboard', endpoint='dashboard_page_route') # Added endpoint name
    @login_required # Protect this page
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

    # Configure Flask-Login's login view after the route is defined
    login_manager.login_view = 'login_page_route_main' # Use the endpoint name for the main login page
    login_manager.login_message_category = "info"


    return app