# server/app/config.py
import os
from dotenv import load_dotenv

# Determine the path to the .env file (assuming it's in the 'server' directory,
# which is one level up from the 'app' directory where this config.py likely resides)
# For server/.env:
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # This should be server/
DOTENV_PATH = os.path.join(BASE_DIR, '.env')
# For server/app/.env (if you moved it):
# DOTENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

print(f"--- PRINT DEBUG [config.py]: Attempting to load .env from: {DOTENV_PATH}")
if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)
    print(f"--- PRINT DEBUG [config.py]: .env file loaded successfully from {DOTENV_PATH}.")
else:
    print(f"--- PRINT DEBUG [config.py]: .env file NOT FOUND at {DOTENV_PATH}. Environment variables must be set manually.")

# Print values directly from os.getenv AFTER attempting to load .env
# This helps confirm if .env loading worked or if they were pre-existing environment vars.
print(f"--- PRINT DEBUG [config.py]: Value of os.getenv('GEMINI_API_KEY') AFTER load_dotenv: {os.getenv('GEMINI_API_KEY')}")
print(f"--- PRINT DEBUG [config.py]: Value of os.getenv('GOOGLE_API_KEY') AFTER load_dotenv: {os.getenv('GOOGLE_API_KEY')}")

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a_very_secret_default_key_for_dev')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ttrpg_app_db')
    
    # API Keys - these MUST be uppercase to be loaded by from_object() into app.config
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') # If you use this as an alternative name
    
    # AI Model Name
    GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-1.5-flash-latest')

    DEBUG = False
    TESTING = False

    # Print what the Config class itself sees for these keys
    print(f"--- PRINT DEBUG [config.py - Config Class Definition]: GEMINI_API_KEY = {GEMINI_API_KEY}")
    print(f"--- PRINT DEBUG [config.py - Config Class Definition]: GOOGLE_API_KEY = {GOOGLE_API_KEY}")
    print(f"--- PRINT DEBUG [config.py - Config Class Definition]: GEMINI_MODEL_NAME = {GEMINI_MODEL_NAME}")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # DevelopmentConfig inherits GEMINI_API_KEY, GOOGLE_API_KEY, GEMINI_MODEL_NAME from Config
    # No need to redefine them unless you want to override for 'dev' environment specifically.
    print(f"--- PRINT DEBUG [config.py - DevelopmentConfig Class Definition]: DEBUG = {DEBUG}")
    print(f"--- PRINT DEBUG [config.py - DevelopmentConfig]: Inherited GEMINI_API_KEY = {Config.GEMINI_API_KEY}")


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    MONGO_URI = os.getenv('TEST_MONGO_URI', 'mongodb://localhost:27017/ttrpg_app_db_test')


class ProductionConfig(Config):
    """Production configuration."""
    # Production specific settings would go here
    # For example, DEBUG and TESTING would be False (already set in base Config)
    pass

# Dictionary to access config classes by name
config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig,
    default=DevelopmentConfig # Default to DevelopmentConfig
)
