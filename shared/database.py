"""
Database connection and session management for the IELTS Telegram Bot.
This module provides database connectivity using SQLAlchemy with MySQL.
"""

import logging
from typing import Optional, Generator, Dict, Any
from contextlib import contextmanager

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker, declarative_base
    from sqlalchemy.exc import SQLAlchemyError, OperationalError
    from sqlalchemy.pool import QueuePool
    SQLALCHEMY_AVAILABLE = True
except ImportError as e:
    print(f"SQLAlchemy import error: {e}")
    SQLALCHEMY_AVAILABLE = False
    # Create dummy classes for development
    class declarative_base:
        pass
    class sessionmaker:
        pass

from .config import config

# Set up logging
logger = logging.getLogger(__name__)

# Create the declarative base for SQLAlchemy models
Base = declarative_base()

class DatabaseManager:
    """
    Database manager class that handles connection pooling and session management.
    """

    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize the database connection and session factory.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not SQLALCHEMY_AVAILABLE:
            logger.error("❌ SQLAlchemy is not available. Please install SQLAlchemy.")
            return False

        try:
            # Create database engine with connection pooling
            self._engine = create_engine(
                config.database_url,
                poolclass=QueuePool,
                pool_size=5,            # Reduced pool size for development
                max_overflow=10,        # Reduced overflow
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=config.LOG_LEVEL.upper() == 'DEBUG',
                connect_args={
                    "charset": "utf8mb4",
                    "autocommit": False,
                }
            )

            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                autoflush=True,
                autocommit=False,
                expire_on_commit=False
            )

            # Test the connection
            if self._test_connection():
                self._initialized = True
                logger.info("✅ Database connection initialized successfully")
                return True
            else:
                logger.error("❌ Database connection test failed")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            return False

    def _test_connection(self) -> bool:
        """
        Test the database connection by executing a simple query.

        Returns:
            bool: True if connection test successful, False otherwise
        """
        try:
            with self._engine.connect() as connection:
                result = connection.execute(text("SELECT 1 as test"))
                test_value = result.scalar()
                return test_value == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    @contextmanager
    def get_session(self):
        """
        Context manager that provides a database session with automatic cleanup.

        Usage:
            with db_manager.get_session() as session:
                # Use session here
                user = session.query(User).first()
        """
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def create_session(self):
        """
        Create a new database session.

        Returns:
            New SQLAlchemy session
        """
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        return self._session_factory()

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the database connection.

        Returns:
            dict: Health check results
        """
        try:
            with self.get_session() as session:
                result = session.execute(text("SELECT 1 as health_check"))
                test_value = result.scalar()

                db_info = session.execute(text("SELECT VERSION() as version")).scalar()

                return {
                    "status": "healthy" if test_value == 1 else "unhealthy",
                    "database_version": db_info,
                    "connection_pool_size": self._engine.pool.size() if self._engine else 0,
                    "checked_out_connections": self._engine.pool.checkedout() if self._engine else 0,
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_pool_size": 0,
                "checked_out_connections": 0,
            }

    def close(self):
        """Close all database connections and cleanup resources."""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")

# Create global database manager instance
db_manager = DatabaseManager()

def init_database() -> bool:
    """Initialize the database connection."""
    return db_manager.initialize()

def get_db_session():
    """Get a database session context manager."""
    return db_manager.get_session()

def create_db_session():
    """Create a new database session."""
    return db_manager.create_session()

def check_database_health() -> Dict[str, Any]:
    """Check database health status."""
    return db_manager.health_check()

def close_database():
    """Close all database connections."""
    db_manager.close()