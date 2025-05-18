# ---- server/app/utils/db.py ----
from flask_pymongo import PyMongo

# Initialize PyMongo. This will be configured with the app instance in __init__.py
mongo = PyMongo()

def init_db(app):
    """
    Initializes the MongoDB connection with the Flask app.
    Args:
        app (Flask): The Flask application instance.
    """
    mongo.init_app(app)
    print("MongoDB initialized.")

# You can add helper functions here to interact with MongoDB collections
# For example:
# def get_user_collection():
#     return mongo.db.users
#
# def get_npc_collection():
#     return mongo.db.npcs
