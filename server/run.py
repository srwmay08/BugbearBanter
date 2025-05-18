# ---- server/run.py ----
import os
from app import create_app

# Determine the configuration to use (e.g., from environment variable)
# Defaults to 'dev' if FLASK_CONFIG is not set.
config_name = os.getenv('FLASK_CONFIG', 'dev')

app = create_app(config_name)

# Make sure to register your blueprints in app/__init__.py
# Example:
from app.routes.auth import auth_bp
app.register_blueprint(auth_bp, url_prefix='/api/auth')

from app.routes.dialogue import dialogue_bp
app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue')


if __name__ == '__main__':
    # Host '0.0.0.0' makes the server accessible externally (e.g., within a Docker container or local network)
    # Debug mode should be handled by the config (app.config['DEBUG'])
    # The port can also be configured
    port = int(os.getenv('PORT', 5001)) # Using 5001 to avoid conflict with React dev server (often 3000) or other apps
    app.run(host='0.0.0.0', port=port)