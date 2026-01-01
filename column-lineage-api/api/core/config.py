"""Configuration settings for the application."""

import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, continue without it
    pass

class Settings:
    """Application settings."""
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    
    # Snowflake settings
    SNOWFLAKE_ACCOUNT: str = os.getenv("SNOWFLAKE_ACCOUNT", "")
    SNOWFLAKE_USER: str = os.getenv("SNOWFLAKE_USER", "")
    SNOWFLAKE_PASSWORD: str = os.getenv("SNOWFLAKE_PASSWORD", "")
    SNOWFLAKE_DATABASE: str = os.getenv("SNOWFLAKE_DATABASE", "")
    SNOWFLAKE_SCHEMA: str = os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC")
    SNOWFLAKE_WAREHOUSE: str = os.getenv("SNOWFLAKE_WAREHOUSE", "")
    SNOWFLAKE_ROLE: str = os.getenv("SNOWFLAKE_ROLE", "")
    
    # JWT settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    
    # Auto-save settings
    AUTO_SAVE_RESULTS: bool = os.getenv("AUTO_SAVE_RESULTS", "true").lower() == "true"
    AUTO_SAVE_TO_DATABASE: bool = os.getenv("AUTO_SAVE_TO_DATABASE", "true").lower() == "true"
    RESULTS_DIRECTORY: str = os.getenv("RESULTS_DIRECTORY", "analysis_results")
    
    # API settings
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Column Lineage API")
    VERSION: str = os.getenv("VERSION", "0.1.0")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")
    RUN_ENV: str = os.getenv("RUN_ENV", "dev")
    
    # Connection mode settings
    POC: bool = os.getenv("POC", "true").lower() == "true"
    
    # CORS settings
    CORS_ORIGINS: list = eval(os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:8080"]'))
    ALLOWED_HOSTS: list = eval(os.getenv("ALLOWED_HOSTS", '["localhost", "127.0.0.1"]'))
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "json")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    def __init__(self):
        # Ensure results directory exists if auto-save is enabled
        if self.AUTO_SAVE_RESULTS:
            Path(self.RESULTS_DIRECTORY).mkdir(exist_ok=True)

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings."""
    return settings