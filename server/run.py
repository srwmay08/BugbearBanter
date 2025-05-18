# ---- server/run.py ----
import os
from app import create_app # create_app now handles blueprint registration

config_name = os.getenv('FLASK_CONFIG', 'dev')
app = create_app(config_name)

# REMOVE these lines if they are still here:
# from app.routes.auth import auth_bp  <-- REMOVE
# app.register_blueprint(auth_bp, url_prefix='/api/auth') <-- REMOVE

# from app.routes.dialogue import dialogue_bp <-- REMOVE
# app.register_blueprint(dialogue_bp, url_prefix='/api/dialogue') <-- REMOVE

# And any other direct blueprint registrations

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port) # Debug mode is handled by your config