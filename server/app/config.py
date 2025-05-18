# ---- server/app/config.py ----
import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
# Create a .env file in the 'server' directory for your secret keys
# Example .env content:
# MONGO_URI="mongodb://localhost:27017/ttrpg_db"
# SECRET_KEY="your_very_secret_key"
# GEMINI_API_KEY="your_gemini_api_key"
# ELEVENLABS_API_KEY="your_elevenlabs_api_key"
# PATREON_CLIENT_ID="your_patreon_client_id"
# PATREON_CLIENT_SECRET="your_patreon_client_secret"

# Configure API Key
# set GOOGLE_API_KEY=AIzaSyDA6jyrhmDpDN7tiK32pzkr_PDqjZBOIY8
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()
if not GOOGLE_API_KEY:
    raise ValueError("Missing API Key. Set it as an environment variable.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

NPC_DIR = "npc_data"


load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'a_default_secret_key_for_development')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ttrpg_app_db')
    DEBUG = False
    TESTING = False
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
    PATREON_CLIENT_ID = os.getenv('PATREON_CLIENT_ID')
    PATREON_CLIENT_SECRET = os.getenv('PATREON_CLIENT_SECRET')
    # Add other configuration variables here


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