# ---- server/run.py ----
import os
from app import create_app # create_app now handles all blueprint registration

config_name = os.getenv('FLASK_CONFIG', 'dev')
app = create_app(config_name)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    # Debug mode is now controlled by your FLASK_CONFIG (e.g., DevelopmentConfig sets DEBUG = True)
    app.run(host='0.0.0.0', port=port)