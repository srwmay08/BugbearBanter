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

    # Initialize extensions
    init_db(app)  # Initialize MongoDB
    CORS(app)     # Enable CORS for all routes, or configure as needed

    # Register blueprints (routes)
    # from .routes.auth import auth_bp
    # app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # from .routes.dialogue import dialogue_bp
    # app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')

    # Add other blueprints for game_worlds, npcs, scenes, etc.
    # from .routes.game_worlds import game_worlds_bp
    # app.register_blueprint(game_worlds_bp, url_prefix='/api/game_worlds')

    # from .routes.npcs import npcs_bp
    # app.register_blueprint(npcs_bp, url_prefix='/api/npcs')


    @app.route('/health')
    def health_check():
        return "API is healthy!", 200

    return app