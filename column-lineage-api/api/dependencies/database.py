"""Database connection dependencies."""

from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker

from api.core.config import get_settings
from api.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache()
def get_database_engine() -> Engine:
    """Get Snowflake database engine."""
    settings = get_settings()
    
    # Skip database connection if Snowflake credentials are not provided
    if not all([
        settings.SNOWFLAKE_ACCOUNT,
        settings.SNOWFLAKE_USER,
        settings.SNOWFLAKE_PASSWORD,
        settings.SNOWFLAKE_DATABASE,
    ]):
        logger.warning("Snowflake credentials not provided, skipping database connection")
        return None
    
    try:
        engine = create_engine(
            settings.snowflake_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        logger.info("Database engine created successfully")
        return engine
        
    except Exception as e:
        logger.error("Failed to create database engine", error=str(e))
        return None


def get_database_session():
    """Get database session dependency."""
    engine = get_database_engine()
    SessionLocal = sessionmaker(bind=engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self):
        self.engine = get_database_engine()
        self.logger = get_logger(self.__class__.__name__)
        self.mock_mode = self.engine is None
        
        if self.mock_mode:
            self.logger.info("Running in mock mode - no database connection")
    
    def get_session(self):
        """Get a new database session."""
        if self.mock_mode:
            return None
        
        SessionLocal = sessionmaker(bind=self.engine)
        return SessionLocal()
    
    def execute_query(self, query: str, params: dict = None):
        """Execute a query and return results."""
        if self.mock_mode:
            self.logger.info("Mock query execution", query=query[:100])
            return []
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, params or {})
                return result.fetchall()
        except Exception as e:
            self.logger.error("Query execution failed", query=query, error=str(e))
            raise
    
    def test_connection(self) -> bool:
        """Test database connection."""
        if self.mock_mode:
            self.logger.info("Mock connection test - returning True")
            return True
        
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            self.logger.error("Database connection test failed", error=str(e))
            return False