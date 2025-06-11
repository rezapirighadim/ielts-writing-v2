"""
Basic command handlers for /start and /help commands.
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from shared.database import get_db_session
from shared.models.user import User
from shared.models.system_log import SystemLog
from messages.persian_messages import PersianMessages
from datetime import datetime

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.

    Python Concept: This is an async function that handles Telegram commands.
    The update parameter contains the message info, context contains bot context.
    """
    try:
        # Get user information from Telegram
        telegram_user = update.effective_user
        telegram_id = telegram_user.id
        username = telegram_user.username
        first_name = telegram_user.first_name
        last_name = telegram_user.last_name

        logger.info(f"Start command from user {telegram_id} (@{username})")

        # Check if user exists in database
        with get_db_session() as session:
            existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()

            if existing_user:
                # Update user activity and info
                existing_user.update_activity()
                existing_user.username = username
                existing_user.first_name = first_name
                existing_user.last_name = last_name

                # Reset monthly usage if needed
                reset_occurred = existing_user.reset_monthly_usage_if_needed()
                if reset_occurred:
                    logger.info(f"Monthly usage reset for user {telegram_id}")

                # Send returning user message
                user_data = existing_user.to_dict()
                message = PersianMessages.format_welcome_returning_user(user_data)

                # Log user activity
                log_entry = SystemLog.create_log(
                    level="INFO",
                    message=f"User {telegram_id} used /start command (returning user)",
                    module="basic_handlers",
                    user_id=existing_user.id,
                    telegram_id=telegram_id
                )
                session.add(log_entry)

            else:
                # Create new user
                new_user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    registration_date=datetime.utcnow(),
                    last_activity=datetime.utcnow()
                )

                session.add(new_user)
                session.flush()  # Get the user ID

                # Send new user message
                message = PersianMessages.START_NEW_USER

                # Log new user registration
                log_entry = SystemLog.create_log(
                    level="INFO",
                    message=f"New user registered: {telegram_id} (@{username})",
                    module="basic_handlers",
                    user_id=new_user.id,
                    telegram_id=telegram_id
                )
                session.add(log_entry)

                logger.info(f"New user registered: {telegram_id} (@{username})")

        # Send the message
        await update.message.reply_text(message)

    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(PersianMessages.ERROR_GENERAL)

        # Log the error
        try:
            with get_db_session() as session:
                error_log = SystemLog.create_log(
                    level="ERROR",
                    message=f"Error in start_command: {str(e)}",
                    module="basic_handlers",
                    telegram_id=telegram_user.id if telegram_user else None
                )
                session.add(error_log)
        except:
            pass  # Don't let logging errors break the handler


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /help command.
    """
    try:
        telegram_user = update.effective_user
        telegram_id = telegram_user.id

        logger.info(f"Help command from user {telegram_id}")

        # Log user activity
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.update_activity()

                    log_entry = SystemLog.create_log(
                        level="INFO",
                        message=f"User {telegram_id} used /help command",
                        module="basic_handlers",
                        user_id=user.id,
                        telegram_id=telegram_id
                    )
                    session.add(log_entry)
        except Exception as e:
            logger.error(f"Error logging help command: {e}")

        # Send help message
        await update.message.reply_text(PersianMessages.HELP)

    except Exception as e:
        logger.error(f"Error in help_command: {e}")
        await update.message.reply_text(PersianMessages.ERROR_GENERAL)


async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle unknown commands.
    """
    try:
        telegram_user = update.effective_user
        telegram_id = telegram_user.id
        command_text = update.message.text

        logger.info(f"Unknown command from user {telegram_id}: {command_text}")

        # Log unknown command
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                user_id = user.id if user else None

                log_entry = SystemLog.create_log(
                    level="WARNING",
                    message=f"Unknown command received: {command_text}",
                    module="basic_handlers",
                    user_id=user_id,
                    telegram_id=telegram_id
                )
                session.add(log_entry)
        except Exception as e:
            logger.error(f"Error logging unknown command: {e}")

        # Send helpful response
        response = """❓ دستور شناخته شده نیست

🔹 دستورات موجود:
- /start - شروع کار با ربات
- /help - راهنمای استفاده
- /submit - ارسال متن برای بررسی
- /stats - آمار شخصی
- /examples - نمونه سوالات
- /channels - کانال‌ها برای درخواست رایگان

برای راهنمای کامل از /help استفاده کنید."""

        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error in unknown_command: {e}")
        await update.message.reply_text(PersianMessages.ERROR_GENERAL)


def register_basic_handlers(application: Application) -> None:
    """
    Register basic command handlers with the application.

    Args:
        application: Telegram Application instance
    """
    try:
        # Register command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))

        logger.info("✅ Basic handlers registered successfully")

    except Exception as e:
        logger.error(f"❌ Failed to register basic handlers: {e}")
        raise