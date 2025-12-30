"""Application configuration management."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Environment
    RUN_ENV: str = Field(default="dev", description="Runtime environment")
    DEBUG: bool = Field(default=True, description="Debug mode")
    
    # API Configuration
    PROJECT_NAME: str = Field(default="Column Lineage API", description="Project name")
    VERSION: str = Field(default="0.1.0", description="API version")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API v1 prefix")
    
    # Security (Optional for testing)
    JWT_SECRET_KEY: str = Field(default="test-secret-key-change-in-production", description="JWT secret key")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_EXPIRE_MINUTES: int = Field(default=30, description="JWT expiration in minutes")
    
    # CORS and Security
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1"],
        description="Allowed hosts"
    )
    
    # Database Configuration (Optional for testing)
    SNOWFLAKE_ACCOUNT: str = Field(default="", description="Snowflake account")
    SNOWFLAKE_USER: str = Field(default="", description="Snowflake user")
    SNOWFLAKE_PASSWORD: str = Field(default="", description="Snowflake password")
    SNOWFLAKE_DATABASE: str = Field(default="", description="Snowflake database")
    SNOWFLAKE_SCHEMA: str = Field(default="", description="Snowflake schema")
    SNOWFLAKE_WAREHOUSE: str = Field(default="", description="Snowflake warehouse")
    SNOWFLAKE_ROLE: str = Field(default="", description="Snowflake role")
    
    # AWS Configuration (Optional for testing)
    AWS_REGION: str = Field(default="us-east-1", description="AWS region")
    AWS_ACCESS_KEY_ID: str = Field(default="", description="AWS access key ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", description="AWS secret access key")
    
    # AWS Cognito (optional)
    COGNITO_USER_POOL_ID: str = Field(default="", description="Cognito user pool ID")
    COGNITO_CLIENT_ID: str = Field(default="", description="Cognito client ID")
    COGNITO_REGION: str = Field(default="us-east-1", description="Cognito region")
    
    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FORMAT: str = Field(default="json", description="Log format")
    
    @property
    def snowflake_url(self) -> str:
        """Generate Snowflake connection URL."""
        if not all([self.SNOWFLAKE_ACCOUNT, self.SNOWFLAKE_USER, self.SNOWFLAKE_PASSWORD]):
            return ""
        
        # URL encode the password to handle special characters
        from urllib.parse import quote_plus
        encoded_password = quote_plus(self.SNOWFLAKE_PASSWORD)
        encoded_user = quote_plus(self.SNOWFLAKE_USER)
        
        # For organization-account format, SQLAlchemy needs specific handling
        # Format: snowflake://user:password@account/database/schema?warehouse=wh&role=role
        return (
            f"snowflake://{encoded_user}:{encoded_password}"
            f"@{self.SNOWFLAKE_ACCOUNT}/"
            f"{self.SNOWFLAKE_DATABASE}/{self.SNOWFLAKE_SCHEMA}"
            f"?warehouse={self.SNOWFLAKE_WAREHOUSE}&role={self.SNOWFLAKE_ROLE}"
        )
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.RUN_ENV.lower() in ("dev", "development", "local")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.RUN_ENV.lower() in ("prod", "production")


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()