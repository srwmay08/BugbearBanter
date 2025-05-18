# ---- server/app/__init__.py ----
from flask import Flask
from flask_cors import CORS
from .config import config_by_name
from .utils.db import init_db

def create_app(config_name='default'):
    """
    Application factory function.
    Args:
        config_name (str): The name of the configuration to use (e.g., 'dev', 'prod').
    Returns:
        Flask: The created Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Route for serving the main index.html file
    # Route for serving the main index.html file
    @app.route('/')
    def index():
        # Use os.path.join for constructing paths robustly
        return send_from_directory(app.static_folder, 'index.html')

    # Route for serving other static files (CSS, JS, images)
    # Flask does this automatically if static_folder is configured correctly
    # and files are requested with a path like /static/css/style.css
    # However, if index.html references css/style.css, it might need adjusting
    # Ensure your index.html references static files like:
    # <link rel="stylesheet" href="/static/css/style.css">
    # <script src="/static/js/app.js"></script>

    @app.route('/static/<path:path>')
    def serve_static(path):
        return send_from_directory(app.static_folder, path)


    @app.route('/health')
    def health_check():
        return "API is healthy!", 200

    # Register blueprints AFTER other app configurations and routes if they depend on them
    # or if you want specific ordering. Usually order of blueprint registration doesn't strictly matter
    # unless one overrides another's routes.
    from app.routes.auth import auth_bp # Moved from run.py
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.routes.dialogue import dialogue_bp # Moved from run.py
    app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')

    return app