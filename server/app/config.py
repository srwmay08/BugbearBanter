# server/app/config.py
import os
from dotenv import load_dotenv
import google.generativeai as genai # Ensure this import is here

dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env') # Points to server/.env

load_dotenv(dotenv_path)
print(f"--- PRINT DEBUG [config.py]: Attempted to load .env from: {dotenv_path}")
print(f"--- PRINT DEBUG [config.py]: GEMINI_API_KEY from os.getenv: {os.getenv('GEMINI_API_KEY')}")
print(f"--- PRINT DEBUG [config.py]: GOOGLE_API_KEY from os.getenv: {os.getenv('GOOGLE_API_KEY')}")

    
# This is where the API key is set for the Flask app config
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') # If you use this as an alternative
GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-1.5-flash-latest')

# Now, check if the Python variable GEMINI_API_KEY is empty
if not GEMINI_API_KEY: # This is your line 11 (or around there)
    raise ValueError("Missing GEMINI_API_KEY. Set it in your .env file or as an environment variable.")

# If the script proceeds, GEMINI_API_KEY has a value
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash") # Assuming you still want this model

# Explicitly print what's being set in the Config class
print(f"--- PRINT DEBUG [config.py - Config Class]: GEMINI_API_KEY = {GEMINI_API_KEY}")
print(f"--- PRINT DEBUG [config.py - Config Class]: GOOGLE_API_KEY = {GOOGLE_API_KEY}")

NPC_DIR = "npc_data"

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a_default_secret_key_for_development')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ttrpg_app_db')
    DEBUG = False
    TESTING = False
    # You can decide if you still need this separate Config.GEMINI_API_KEY or if the one above is sufficient
    # If the GEMINI_API_KEY loaded above is the one you want to use throughout,
    # you might not need to fetch it again here unless it serves a different purpose.
    # For now, let's assume the GEMINI_API_KEY above is the primary one.
    # You could reference it here or fetch it again if necessary.
    # Example: self.GEMINI_API_KEY = GEMINI_API_KEY (if you want to store it in the config object)
    # Or, if it's only used for genai.configure, you might not need it in the Config class instances.

    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    PATREON_CLIENT_ID = os.getenv('PATREON_CLIENT_ID')
    PATREON_CLIENT_SECRET = os.getenv('PATREON_CLIENT_SECRET')
    # Add other configuration variables here

# ... rest of your config file (DevelopmentConfig, TestingConfig, etc.) ...

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    MONGO_URI = os.getenv('TEST_MONGO_URI', 'mongodb://localhost:27017/ttrpg_app_db_test')

class ProductionConfig(Config):
    """Production configuration."""
    # Production specific settings
    pass

# Dictionary to access config classes by name
config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig,
    default=DevelopmentConfig
)