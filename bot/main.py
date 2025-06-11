"""
Main entry point for the IELTS Writing Practice Telegram Bot.
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.logging_config import setup_logging
from config.bot_config import bot_config
from shared.config import validate_environment
from shared.database import init_database, close_database
from handlers.basic_handlers import register_basic_handlers
from handlers.error_handler import register_error_handler

# Set up logging first
setup_logging()
logger = logging.getLogger(__name__)

class BotApplication:
    """Main bot application class that manages the bot lifecycle."""

    def __init__(self):
        self.application = None
        self.running = False

    async def initialize(self) -> bool:
        """Initialize all bot components."""
        logger.info("🚀 Initializing IELTS Telegram Bot...")

        # Step 1: Validate environment
        logger.info("1. Validating environment configuration...")
        if not validate_environment():
            logger.error("❌ Environment validation failed")
            return False
        logger.info("   ✅ Environment configuration valid")

        # Step 2: Initialize database
        logger.info("2. Connecting to database...")
        if not init_database():
            logger.error("❌ Database initialization failed")
            return False
        logger.info("   ✅ Database connected successfully")

        # Step 3: Create Telegram application
        logger.info("3. Creating Telegram bot application...")
        try:
            self.application = bot_config.create_application()
            logger.info("   ✅ Telegram application created")
        except Exception as e:
            logger.error(f"❌ Failed to create Telegram application: {e}")
            return False

        # Step 4: Register handlers
        logger.info("4. Registering command handlers...")
        await self.register_handlers()
        logger.info("   ✅ Handlers registered")

        logger.info("🎉 Bot initialization completed successfully!")
        return True

    async def register_handlers(self):
        """Register all bot command and message handlers."""
        try:
            # Register basic handlers (/start, /help)
            register_basic_handlers(self.application)

            # Register error handler
            register_error_handler(self.application)

            logger.info("   ✅ All handlers registered successfully")

        except Exception as e:
            logger.error(f"❌ Failed to register handlers: {e}")
            raise

    async def start(self):
        """Start the bot and begin polling for messages."""
        if not self.application:
            logger.error("❌ Bot not initialized. Call initialize() first.")
            return False

        try:
            logger.info("▶️ Starting bot polling...")
            self.running = True

            # Initialize and start the application
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            logger.info("✅ Bot is now running and listening for messages!")
            logger.info("📱 Users can now interact with the bot")
            logger.info("Press Ctrl+C to stop the bot")

            # Keep the bot running
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Error while running bot: {e}")
            return False
        finally:
            await self.stop()

    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("⏹️ Stopping bot...")
        self.running = False

        if self.application:
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("✅ Bot stopped successfully")
            except Exception as e:
                logger.error(f"❌ Error stopping bot: {e}")

        # Close database connections
        close_database()
        logger.info("✅ Database connections closed")

    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main function that runs the bot application."""
    print("🤖 IELTS Writing Practice Telegram Bot")
    print("=" * 50)

    # Create bot application
    bot_app = BotApplication()

    # Set up signal handlers for graceful shutdown
    bot_app.setup_signal_handlers()

    try:
        # Initialize the bot
        if not await bot_app.initialize():
            logger.error("❌ Bot initialization failed")
            sys.exit(1)

        # Start the bot
        await bot_app.start()

    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        # Ensure cleanup
        await bot_app.stop()

if __name__ == "__main__":
    """Entry point when script is run directly."""
    try:
        # Run the async main function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)