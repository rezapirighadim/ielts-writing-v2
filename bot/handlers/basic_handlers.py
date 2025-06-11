"""
Basic command handlers for /start and /help commands.
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from .user_handler import handle_user_registration_flow, log_user_action
from .user_utils import get_user_by_telegram_id
from messages.persian_messages import PersianMessages

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command with improved user registration.
    """
    try:
        # Handle user registration flow
        user = await handle_user_registration_flow(update, context)

        # Log the start command usage
        await log_user_action(user, "start_command", f"User used /start command")

        logger.info(f"Start command completed for user {user.telegram_id}")

    except Exception as e:
        logger.error(f"Error in start_command: {e}")
        await update.message.reply_text(PersianMessages.ERROR_GENERAL)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /help command.
    """
    try:
        telegram_user = update.effective_user
        telegram_id = telegram_user.id

        logger.info(f"Help command from user {telegram_id}")

        # Get user from database
        user = get_user_by_telegram_id(telegram_id)
        if user:
            await log_user_action(user, "help_command", "User viewed help")

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
        command_text = update.message.text

        logger.info(f"Unknown command from user {telegram_user.id}: {command_text}")

        # Get user and log unknown command
        user = get_user_by_telegram_id(telegram_user.id)
        if user:
            await log_user_action(user, "unknown_command", f"Command: {command_text}")

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
    """
    try:
        # Register command handlers
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))

        logger.info("✅ Basic handlers registered successfully")

    except Exception as e:
        logger.error(f"❌ Failed to register basic handlers: {e}")
        raise