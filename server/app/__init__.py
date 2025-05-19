# server/app/__init__.py
from flask import Flask, send_from_directory, abort
from flask_cors import CORS
# Ensure .config is imported before it's used.
from .config import config_by_name # This line imports your config.py
from .utils.db import init_db
import os

def create_app(config_name='default'):
    print(f"--- PRINT DEBUG [__init__.py - create_app]: Using config_name: {config_name}")
    
    app = Flask(__name__, static_folder='../static')
    
    # Load configuration object
    # The config_by_name[config_name] should be an object (e.g., DevelopmentConfig)
    # whose uppercase attributes are loaded into app.config
    selected_config_object = config_by_name[config_name]
    app.config.from_object(selected_config_object)
    print(f"--- PRINT DEBUG [__init__.py - create_app]: Loaded config from object: {selected_config_object.__name__}")

    # --- CRITICAL DEBUG: Inspect app.config AFTER loading ---
    print("--- PRINT DEBUG [__init__.py - create_app]: Inspecting app.config items: ---")
    for key, value in app.config.items():
        # We are particularly interested in GEMINI_API_KEY or GOOGLE_API_KEY
        if "API_KEY" in key.upper() or "MODEL_NAME" in key.upper() or "MONGO_URI" in key.upper() or "DEBUG" in key.upper():
            print(f"    app.config['{key}'] = {value}")
    print("--- PRINT DEBUG [__init__.py - create_app]: End of app.config inspection ---")
    # --- END CRITICAL DEBUG ---

    init_db(app) 
    CORS(app)    

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .routes.dialogue import dialogue_bp # Using version from dialogue_routes_final_debug
    app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')

    from .routes.npcs import npcs_bp
    app.register_blueprint(npcs_bp, url_prefix='/api/npcs')

    @app.route('/')
    def index_page():
        # ... (as before)
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'index.html')
        if not os.path.exists(target_path):
            abort(404)
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/scene')
    def scene_page():
        # ... (as before)
        absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
        target_path = os.path.join(absolute_static_folder, 'scene.html')
        if not os.path.exists(target_path):
            abort(404)
        return send_from_directory(app.static_folder, 'scene.html')

    @app.route('/health')
    def health_check():
        return "API is healthy!", 200

    return app
