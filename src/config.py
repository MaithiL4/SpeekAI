"""
Configuration management for the application
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # API Keys
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Keep for now in case we switch back
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    
    # Model Configuration
    DEEPGRAM_MODEL = "nova-2"
    MISTRAL_MODEL = "mistral-small-latest" # Using Mistral for response generation
    
    # Application Settings
    MAX_AUDIO_SIZE_MB = 100
    ALLOWED_AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.ogg', '.flac']
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.DEEPGRAM_API_KEY:
            raise ValueError("DEEPGRAM_API_KEY not found in environment")
        if not cls.MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY not found in environment")
        
        return True

# Validate on import
Config.validate()