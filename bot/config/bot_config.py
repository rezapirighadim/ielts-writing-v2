"""
Bot-specific configuration and settings.
"""

import logging
from telegram.ext import Application
from shared.config import config

logger = logging.getLogger(__name__)

class BotConfig:
    """
    Bot configuration class that manages Telegram bot settings.
    """

    def __init__(self):
        self.token = config.TELEGRAM_BOT_TOKEN
        self.application = None
        self._initialized = False

    def validate_token(self) -> bool:
        """
        Validate that bot token is present and has correct format.
        """
        if not self.token:
            logger.error("❌ Bot token is not set in environment variables")
            return False

        token = self.token

        # Remove 'bot' prefix if present (optional)
        if token.startswith('bot'):
            token = token[3:]

        if ':' not in token:
            logger.error("❌ Bot token format appears invalid - missing colon")
            return False

        parts = token.split(':')
        if len(parts) != 2:
            logger.error("❌ Bot token format appears invalid - incorrect format")
            return False

        bot_id_part, token_part = parts

        # Bot ID should be numeric
        if not bot_id_part.isdigit():
            logger.error("❌ Bot token format appears invalid - bot ID not numeric")
            return False

        # Token part should be at least 30 characters
        if len(token_part) < 30:
            logger.error("❌ Bot token format appears invalid - token part too short")
            return False

        logger.info("✅ Bot token format is valid")
        return True

    def create_application(self) -> Application:
        """
        Create and configure Telegram Application instance.
        """
        if not self.validate_token():
            raise ValueError("Invalid bot token")

        # Create application with bot token - simplified approach
        application = Application.builder().token(self.token).build()

        self.application = application
        self._initialized = True

        logger.info("✅ Telegram application created successfully")
        return application

    def get_application(self) -> Application:
        """Get the Telegram application instance."""
        if not self._initialized:
            return self.create_application()

        return self.application

    @property
    def is_ready(self) -> bool:
        """Check if bot configuration is ready."""
        return self._initialized and self.application is not None

# Global bot config instance
bot_config = BotConfig()