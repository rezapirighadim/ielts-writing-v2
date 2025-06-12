"""
Shared configuration module for the IELTS Telegram Bot project.
This module handles environment variables and provides configuration
settings for both the bot and admin panel.
"""

import os
import logging
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logger for this module
logger = logging.getLogger(__name__)


class Config:
    """
    Configuration class that centralizes all environment variables
    and provides type-safe access to configuration values.

    Python Concept: Class-based configuration is a common pattern
    that makes it easy to manage settings across the application.
    """

    # Database Configuration
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '3306'))
    DB_NAME: str = os.getenv('DB_NAME', 'ielts_bot_db')
    DB_USER: str = os.getenv('DB_USER', '')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')

    # Bot Configuration
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    BOT_TOKEN: str = TELEGRAM_BOT_TOKEN  # Alias for compatibility

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    OPENAI_MAX_RETRIES: int = int(os.getenv('OPENAI_MAX_RETRIES', '3'))
    OPENAI_RETRY_DELAY: float = float(os.getenv('OPENAI_RETRY_DELAY', '1.0'))
    OPENAI_TIMEOUT: int = int(os.getenv('OPENAI_TIMEOUT', '60'))

    # Admin Panel Configuration
    DJANGO_SECRET_KEY: str = os.getenv('DJANGO_SECRET_KEY', 'change-me-in-production')
    DJANGO_DEBUG: bool = os.getenv('DJANGO_DEBUG', 'True').lower() == 'true'
    DJANGO_ALLOWED_HOSTS: List[str] = os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

    # Usage Limits Configuration
    FREE_MONTHLY_LIMIT: int = int(os.getenv('FREE_MONTHLY_LIMIT', '10'))
    PREMIUM_MONTHLY_LIMIT: int = int(os.getenv('PREMIUM_MONTHLY_LIMIT', '100'))
    CHANNEL_BONUS_REQUESTS: int = int(os.getenv('CHANNEL_BONUS_REQUESTS', '5'))
    MAX_BONUS_REQUESTS: int = int(os.getenv('MAX_BONUS_REQUESTS', '20'))

    # Telegram Channels Configuration
    TELEGRAM_CHANNELS: List[str] = [
        channel.strip()
        for channel in os.getenv('TELEGRAM_CHANNELS', '').split(',')
        if channel.strip()
    ]

    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')

    @property
    def database_url(self) -> str:
        """
        Constructs the database URL for MySQL connection.

        Python Concept: @property decorator makes this method accessible
        like an attribute (config.database_url instead of config.database_url())
        """
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @classmethod
    def validate_required_settings(cls) -> bool:
        """
        Validates that all required environment variables are set.

        Python Concept: @classmethod allows calling this method on the class
        itself without creating an instance.

        Returns:
            bool: True if all required settings are present, False otherwise
        """
        required_settings = [
            ('TELEGRAM_BOT_TOKEN', cls().TELEGRAM_BOT_TOKEN),
            ('OPENAI_API_KEY', cls().OPENAI_API_KEY),
            ('DB_USER', cls().DB_USER),
            ('DB_PASSWORD', cls().DB_PASSWORD),
        ]

        missing_settings = []
        for setting_name, setting_value in required_settings:
            if not setting_value:
                missing_settings.append(setting_name)

        if missing_settings:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing_settings)}")
            return False

        logger.info("✅ All required environment variables are set")
        return True

    def __str__(self) -> str:
        """
        String representation for debugging (without sensitive data).

        Python Concept: __str__ method defines how the object appears
        when converted to string or converted to string.
        """
        return f"Config(DB_HOST={self.DB_HOST}, DB_NAME={self.DB_NAME}, LOG_LEVEL={self.LOG_LEVEL})"


# Create a global config instance
config = Config()


# Validation function that can be imported and used
def validate_environment() -> bool:
    """
    Validates the environment configuration.
    This function can be called at application startup.
    """
    return Config.validate_required_settings()