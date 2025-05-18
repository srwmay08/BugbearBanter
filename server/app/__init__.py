# ---- server/app/__init__.py ----
from flask import Flask, send_from_directory
from flask_cors import CORS
from .config import config_by_name
from .utils.db import init_db
import os

def create_app(config_name='default'):
    # The static_folder path '../static' assumes your 'static' directory
    # is a sibling to your 'app' directory.
    # server/
    # ├── app/  (contains this __init__.py)
    # ├── static/
    # └── run.py
    app = Flask(__name__, static_folder='../static')
    app.config.from_object(config_by_name[config_name])

    init_db(app) # Initialize MongoDB
    CORS(app)    # Enable CORS

    # --- Import and Register Blueprints ---
    # Each blueprint should be imported and registered only ONCE.

    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .routes.dialogue import dialogue_bp
    app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')

    # If you have created app/routes/npcs.py with an npcs_bp for your NPC frontend:
    # from .routes.npcs import npcs_bp
    # app.register_blueprint(npcs_bp, url_prefix='/api/npcs')
    # (Ensure this file and blueprint exist if you uncomment it)

    # --- Route for serving the main frontend page (index.html) ---
    @app.route('/')
    def index():
        # This will serve 'index.html' from your 'static' folder.
        # Make sure 'index.html' exists in server/static/index.html
        return send_from_directory(app.static_folder, 'index.html')

    # Flask will automatically handle serving other files (CSS, JS, images)
    # from the 'static_folder' if they are requested with a URL starting
    # with '/static/' (e.g., your index.html should use <link href="/static/css/style.css">).

    # --- Health Check Route ---
    @app.route('/health')
    def health_check():
        return "API is healthy!", 200

    return app