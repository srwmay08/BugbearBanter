# ---- server/app/__init__.py ----
# ... other imports ...
from flask import Flask, send_from_directory
import os

def create_app(config_name='default'):
    app = Flask(__name__, static_folder='../static')
    # ... other app configurations ...

    # Register Blueprints here
    from .routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .routes.dialogue import dialogue_bp
    app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')

    # If you added the npcs_bp for the NPC list:
    from .routes.npcs import npcs_bp
    app.register_blueprint(npcs_bp, url_prefix='/api/npcs')

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