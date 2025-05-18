# ---- server/app/__init__.py ----
from flask import Flask, send_from_directory, abort # Added abort
from flask_cors import CORS
from .config import config_by_name
from .utils.db import init_db # Ensure this is correctly initializing PyMongo
import os

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='../static') # Assumes static is sibling to app
    app.config.from_object(config_by_name[config_name])

    # --- Debug Prints (can be removed once stable) ---
    absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
    # print(f"--- DEBUG: Flask app.static_folder is set to: {app.static_folder}")
    # print(f"--- DEBUG: Absolute static_folder path is: {absolute_static_folder}")
    # print(f"--- DEBUG: Expected index.html path: {os.path.join(absolute_static_folder, 'index.html')}")
    # print(f"--- DEBUG: Expected scene.html path: {os.path.join(absolute_static_folder, 'scene.html')}")


    init_db(app) # Initialize MongoDB
    CORS(app)    # Enable CORS

    # --- Import and Register Blueprints ---
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .routes.dialogue import dialogue_bp
    app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')

    # Assuming you have app/routes/npcs.py with an npcs_bp
    from .routes.npcs import npcs_bp
    app.register_blueprint(npcs_bp, url_prefix='/api/npcs')

    # --- Route for serving the main NPC selection page (index.html) ---
    @app.route('/')
    def index_page(): # Renamed from 'index' to avoid conflict if 'index' is a common var name
        target_path = os.path.join(absolute_static_folder, 'index.html')
        # print(f"--- DEBUG [index_page route]: Attempting to serve '{target_path}'")
        if not os.path.exists(target_path):
            # print(f"--- ERROR [index_page route]: File does NOT exist at '{target_path}'")
            abort(404)
        # print(f"--- DEBUG [index_page route]: File found. Attempting to send.")
        return send_from_directory(app.static_folder, 'index.html')

    # --- Route for serving the new Scene page (scene.html) ---
    @app.route('/scene')
    def scene_page():
        target_path = os.path.join(absolute_static_folder, 'scene.html')
        # print(f"--- DEBUG [scene_page route]: Attempting to serve '{target_path}'")
        if not os.path.exists(target_path):
            # print(f"--- ERROR [scene_page route]: File does NOT exist at '{target_path}'")
            abort(404)
        # print(f"--- DEBUG [scene_page route]: File found. Attempting to send.")
        return send_from_directory(app.static_folder, 'scene.html')


    # --- Health Check Route ---
    @app.route('/health')
    def health_check():
        return "API is healthy!", 200

    return app
