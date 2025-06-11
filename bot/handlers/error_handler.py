"""
Error handling for bot operations.
"""

import logging
import traceback
from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db_session
from shared.models.system_log import SystemLog
from messages.persian_messages import PersianMessages

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle errors that occur during bot operation.

    Python Concept: This is a global error handler that catches
    unhandled exceptions in other handlers.
    """
    try:
        # Log the error
        logger.error("Exception while handling an update:", exc_info=context.error)

        # Get error details
        error_message = str(context.error)
        error_traceback = traceback.format_exc()

        # Get user information if available
        telegram_id = None
        user_id = None

        if isinstance(update, Update) and update.effective_user:
            telegram_id = update.effective_user.id

            # Try to get user from database
            try:
                with get_db_session() as session:
                    from shared.models.user import User
                    user = session.query(User).filter_by(telegram_id=telegram_id).first()
                    if user:
                        user_id = user.id
            except:
                pass

        # Log error to database
        try:
            with get_db_session() as session:
                error_log = SystemLog.create_log(
                    level="ERROR",
                    message=f"Bot error: {error_message}\n\nTraceback:\n{error_traceback}",
                    module="error_handler",
                    user_id=user_id,
                    telegram_id=telegram_id
                )
                session.add(error_log)
        except Exception as db_error:
            logger.error(f"Failed to log error to database: {db_error}")

        # Send user-friendly error message if this was triggered by a user action
        if isinstance(update, Update) and update.effective_chat:
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=PersianMessages.ERROR_GENERAL
                )
            except Exception as send_error:
                logger.error(f"Failed to send error message to user: {send_error}")

    except Exception as handler_error:
        logger.error(f"Error in error handler: {handler_error}")


def register_error_handler(application) -> None:
    """
    Register the global error handler.

    Args:
        application: Telegram Application instance
    """
    try:
        application.add_error_handler(error_handler)
        logger.info("✅ Error handler registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register error handler: {e}")
        raise