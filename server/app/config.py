# ---- server/app/config.py ----
import os
from dotenv import load_dotenv
import google.generativeai as genai # Make sure this import is present

load_dotenv() # <<< MOVED HERE - Load environment variables from .env FIRST

# Configure API Key for Google Generative AI
# This key is used for genai.configure()
GEMINI = os.getenv("GEMINI", "").strip()
if not GEMINI_API_KEY:
    raise ValueError("Missing GEMINI. Set it in your .env file or as an environment variable.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

NPC_DIR = "npc_data"

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a_default_secret_key_for_development')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ttrpg_app_db')
    DEBUG = False
    TESTING = False
    # This is a separate key, potentially for other uses or if you want to use a different name in .env for Flask config
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    PATREON_CLIENT_ID = os.getenv('PATREON_CLIENT_ID')
    PATREON_CLIENT_SECRET = os.getenv('PATREON_CLIENT_SECRET')
    # Add other configuration variables here

# ... rest of your config.py file (DevelopmentConfig, TestingConfig, etc.) ...

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