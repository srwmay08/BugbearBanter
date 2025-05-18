# ---- server/app/__init__.py ----
from flask import Flask, send_from_directory, abort # Add abort
from flask_cors import CORS
from .config import config_by_name
from .utils.db import init_db
import os

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='../static')
    app.config.from_object(config_by_name[config_name])

    absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
    print(f"--- DEBUG: Flask app.static_folder is set to: {app.static_folder}")
    print(f"--- DEBUG: Absolute static_folder path is: {absolute_static_folder}")
    print(f"--- DEBUG: Expected index.html path: {os.path.join(absolute_static_folder, 'index.html')}")

    init_db(app)
    CORS(app)

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .routes.dialogue import dialogue_bp
    app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')

    from .routes.npcs import npcs_bp
    app.register_blueprint(npcs_bp, url_prefix='/api/npcs')

    @app.route('/')
    def index():
        # --- MORE DEBUGGING ---
        target_path = os.path.join(absolute_static_folder, 'index.html')
        print(f"--- DEBUG [index route]: Attempting to serve '{target_path}'")
        if not os.path.exists(target_path):
            print(f"--- ERROR [index route]: File does NOT exist at '{target_path}' according to os.path.exists()")
            abort(404) # Explicitly abort if Python itself can't find it
        if not os.path.isfile(target_path):
            print(f"--- ERROR [index route]: Path exists but is NOT a file at '{target_path}' according to os.path.isfile()")
            abort(404) # Explicitly abort if it's not a file
        print(f"--- DEBUG [index route]: File found at '{target_path}'. Attempting to send with send_from_directory.")
        # --- END MORE DEBUGGING ---
        try:
            return send_from_directory(app.static_folder, 'index.html')
        except Exception as e:
            print(f"--- ERROR [index route]: send_from_directory failed: {e}")
            abort(500)


    @app.route('/health')
    def health_check():
        return "API is healthy!", 200

    return app