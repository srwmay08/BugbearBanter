# ---- server/app/__init__.py ----
from flask import Flask, send_from_directory
from flask_cors import CORS
from .config import config_by_name
from .utils.db import init_db
import os # Make sure os is imported

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='../static')
    app.config.from_object(config_by_name[config_name])

    # --- DEBUG PRINT ---
    # Get the absolute path of the static folder
    # __file__ is the path to this __init__.py file
    # os.path.dirname(__file__) is the 'app' directory
    # os.path.join(os.path.dirname(__file__), app.static_folder) gives the intended path
    # os.path.abspath() makes it an absolute path
    absolute_static_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), app.static_folder))
    print(f"--- DEBUG: Flask app.static_folder is set to: {app.static_folder}")
    print(f"--- DEBUG: Absolute static_folder path is: {absolute_static_folder}")
    print(f"--- DEBUG: Expected index.html path: {os.path.join(absolute_static_folder, 'index.html')}")
    # --- END DEBUG PRINT ---

    init_db(app)
    CORS(app)

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .routes.dialogue import dialogue_bp
    app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')

    # ... (other blueprint registrations like npcs_bp if you have it) ...

    @app.route('/')
    def index():
        # --- DEBUG PRINT for index route ---
        print(f"--- DEBUG: Attempting to serve index.html from {app.static_folder}")
        # --- END DEBUG PRINT ---
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/health')
    def health_check():
        return "API is healthy!", 200

    return app