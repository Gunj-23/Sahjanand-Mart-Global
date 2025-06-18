import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or os.path.join(BASE_DIR, 'data', 'sahjanand_mart.db')
    DATABASE = DATABASE_PATH
    
    # Flask settings
    DEBUG = False
    TESTING = False
    
    # Application settings
    APP_NAME = "Sahjanand Mart"
    APP_VERSION = "1.0.0"

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SECRET_KEY = 'dev-secret-key'

class ProductionConfig(Config):
    """Production configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for production environment")

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DATABASE = ':memory:'  # Use in-memory database for tests

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}