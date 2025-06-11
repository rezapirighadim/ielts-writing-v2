"""
Channel membership and bonus request handlers.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from session.session_utils import (
    get_user_session_from_update,
    set_user_conversation_step,
    reset_user_conversation
)
from session.conversation_state import ConversationStep
from channels.channel_manager import ChannelManager
from channels.verification_utils import (
    verify_user_membership,
    get_channel_bonus_info,
    format_channel_list_message,
    format_membership_verification_message,
    verify_user_in_channel_by_callback
)
from limits.limit_utils import get_user_limit_info_from_update, format_limit_message
from messages.persian_messages import PersianMessages

logger = logging.getLogger(__name__)


async def channels_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /channels command - show available channels for bonus requests.

    Python Concept: This handler shows users available channels and
    provides interface for membership verification and bonus collection.
    """
    try:
        # Get user session
        session = get_user_session_from_update(update)
        if not session:
            await update.message.reply_text("لطفاً ابتدا از دستور /start استفاده کنید")
            return

        # Set conversation state
        set_user_conversation_step(update, ConversationStep.CHANNEL_CHECKING)

        # Get channel bonus information
        channel_info = get_channel_bonus_info(session.user_id)

        if not channel_info.get("success", False):
            await update.message.reply_text(
                "خطا در دریافت اطلاعات کانال‌ها. لطفاً بعداً تلاش کنید."
            )
            reset_user_conversation(update)
            return

        # Check if there are any channels
        available_channels = channel_info.get("available_channels", [])
        if not available_channels:
            message = """📢 درحال حاضر کانالی برای دریافت درخواست رایگان موجود نیست.

💡 به زودی کانال‌های جدید اضافه خواهند شد.
📝 در حال حاضر می‌توانید از /submit برای ارسال متن استفاده کنید."""

            await update.message.reply_text(message)
            reset_user_conversation(update)
            return

        # Format channel list message
        channels_message = format_channel_list_message(channel_info)

        # Create inline keyboard for channel verification
        keyboard = []

        # Add button for checking all channels
        total_potential_bonus = channel_info.get("total_potential_bonus", 0)
        if total_potential_bonus > 0:
            keyboard.append([
                InlineKeyboardButton(
                    f"🔍 بررسی عضویت در همه کانال‌ها (+{total_potential_bonus})",
                    callback_data="verify_all_channels"
                )
            ])

        # Add buttons for individual channels (limit to top 3)
        bonus_eligible_channels = [
                                      ch for ch in available_channels
                                      if ch.get('can_get_bonus', False)
                                  ][:3]

        for channel in bonus_eligible_channels:
            channel_title = channel.get('channel_title', 'نامشخص')
            channel_username = channel.get('channel_username', '')
            bonus_amount = channel.get('bonus_requests', 0)

            button_text = f"🔍 {channel_title} (+{bonus_amount})"
            callback_data = f"verify_channel:{channel_username}"

            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

        # Add utility buttons
        keyboard.extend([
            [InlineKeyboardButton("📊 مشاهده وضعیت درخواست‌ها", callback_data="view_limit_status")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel_channel_operation")]
        ])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            channels_message,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

        logger.info(f"Channels command used by user {session.telegram_id}")

    except Exception as e:
        logger.error(f"Error in channels_command: {e}")
        await update.message.reply_text(PersianMessages.ERROR_GENERAL)
        reset_user_conversation(update)


async def handle_channel_verification_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback queries for channel verification.

    Python Concept: This handles inline keyboard button presses
    for channel membership verification and bonus collection.
    """
    try:
        query = update.callback_query
        await query.answer()

        callback_data = query.data
        session = get_user_session_from_update(update)

        if not session:
            await query.edit_message_text("جلسه منقضی شده. لطفاً دوباره /channels را اجرا کنید.")
            return

        # Handle different callback actions
        if callback_data == "verify_all_channels":
            await handle_verify_all_channels(update, context, session)

        elif callback_data.startswith("verify_channel:"):
            await handle_verify_single_channel(update, context, session, callback_data)

        elif callback_data == "view_limit_status":
            await handle_view_limit_status(update, context, session)

        elif callback_data == "cancel_channel_operation":
            await handle_cancel_channel_operation(update, context, session)

        else:
            await query.edit_message_text("عملیات نامشخص")
            reset_user_conversation(update)

    except Exception as e:
        logger.error(f"Error in handle_channel_verification_callback: {e}")
        await update.callback_query.edit_message_text(
            "خطا در پردازش درخواست. لطفاً دوباره تلاش کنید."
        )
        reset_user_conversation(update)


async def handle_verify_all_channels(update: Update, context: ContextTypes.DEFAULT_TYPE, session) -> None:
    """Handle verification of all channels."""
    try:
        query = update.callback_query

        # Show processing message
        await query.edit_message_text("🔄 در حال بررسی عضویت در تمام کانال‌ها...\nلطفاً چند لحظه صبر کنید.")

        # Set conversation state to processing
        set_user_conversation_step(update, ConversationStep.CHANNEL_BONUS_PROCESSING)

        # Verify membership in all channels
        verification_result = await verify_user_membership(
            update=update,
            bot=context.bot
        )

        # Format and send result
        result_message = format_membership_verification_message(verification_result)

        # Create follow-up keyboard
        keyboard = []

        if verification_result.get("success", False):
            total_bonuses = verification_result.get("total_bonuses_granted", 0)
            available_submissions = verification_result.get("available_submissions", 0)

            if total_bonuses > 0:
                keyboard.append([
                    InlineKeyboardButton("📝 ارسال متن برای بررسی", callback_data="start_submission")
                ])

            keyboard.append([
                InlineKeyboardButton("📊 مشاهده وضعیت کامل", callback_data="view_full_status")
            ])

        keyboard.append([
            InlineKeyboardButton("🔙 بازگشت به کانال‌ها", callback_data="back_to_channels")
        ])

        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

        await query.edit_message_text(
            result_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

        # Reset conversation state
        reset_user_conversation(update)

        logger.info(f"All channels verification completed for user {session.telegram_id}")

    except Exception as e:
        logger.error(f"Error in handle_verify_all_channels: {e}")
        await update.callback_query.edit_message_text(
            "خطا در بررسی عضویت کانال‌ها. لطفاً دوباره تلاش کنید."
        )


async def handle_verify_single_channel(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                       session, callback_data: str) -> None:
    """Handle verification of a single channel."""
    try:
        query = update.callback_query

        # Extract channel username from callback data
        channel_username = callback_data.split(":", 1)[1]

        # Show processing message
        await query.edit_message_text(f"🔄 در حال بررسی عضویت در کانال...\nلطفاً چند لحظه صبر کنید.")

        # Verify membership in specific channel
        verification_result = await verify_user_membership(
            update=update,
            bot=context.bot,
            channel_username=channel_username
        )

        # Format result message
        if verification_result.get("success", False):
            bonus_granted = verification_result.get("bonus_granted", 0)
            channel_title = verification_result.get("channel_title", "کانال")

            if bonus_granted > 0:
                result_message = f"""🎉 تبریک!

✅ عضویت شما در {channel_title} تأیید شد
🎁 {bonus_granted} درخواست رایگان به حساب شما اضافه شد

📊 اکنون می‌توانید متن خود را برای بررسی ارسال کنید."""
            else:
                result_message = f"""✅ عضویت تأیید شد

عضویت شما در {channel_title} تأیید شد.
💡 شما قبلاً درخواست رایگان این کانال را دریافت کرده‌اید."""
        else:
            error_message = verification_result.get("message", "خطا در بررسی عضویت")
            result_message = f"❌ {error_message}"

        # Create follow-up keyboard
        keyboard = [
            [InlineKeyboardButton("🔍 بررسی کانال‌های دیگر", callback_data="back_to_channels")],
            [InlineKeyboardButton("📝 ارسال متن", callback_data="start_submission")],
            [InlineKeyboardButton("📊 وضعیت درخواست‌ها", callback_data="view_limit_status")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            result_message,
            reply_markup=reply_markup
        )

        logger.info(
            f"Single channel verification completed for user {session.telegram_id}, channel: {channel_username}")

    except Exception as e:
        logger.error(f"Error in handle_verify_single_channel: {e}")
        await update.callback_query.edit_message_text(
            "خطا در بررسی عضویت کانال. لطفاً دوباره تلاش کنید."
        )


async def handle_view_limit_status(update: Update, context: ContextTypes.DEFAULT_TYPE, session) -> None:
    """Handle viewing limit status."""
    try:
        query = update.callback_query

        # Get user limit information
        limit_info = get_user_limit_info_from_update(update)
        status_message = format_limit_message(limit_info)

        # Create keyboard
        keyboard = [
            [InlineKeyboardButton("🔍 بررسی عضویت کانال‌ها", callback_data="back_to_channels")],
            [InlineKeyboardButton("📝 ارسال متن", callback_data="start_submission")],
            [InlineKeyboardButton("💎 ارتقاء اکانت", callback_data="upgrade_account")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            status_message,
            reply_markup=reply_markup
        )

    except Exception as e:
        logger.error(f"Error in handle_view_limit_status: {e}")
        await update.callback_query.edit_message_text("خطا در نمایش وضعیت")


async def handle_cancel_channel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE, session) -> None:
    """Handle canceling channel operations."""
    try:
        query = update.callback_query

        await query.edit_message_text(
            "عملیات لغو شد.\n\n" +
            "💡 برای مشاهده کانال‌ها: /channels\n" +
            "📝 برای ارسال متن: /submit\n" +
            "📊 برای مشاهده آمار: /stats"
        )

        reset_user_conversation(update)

    except Exception as e:
        logger.error(f"Error in handle_cancel_channel_operation: {e}")
        await update.callback_query.edit_message_text("عملیات لغو شد")


async def handle_common_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle common callback queries that can appear in multiple contexts.
    """
    try:
        query = update.callback_query
        callback_data = query.data

        if callback_data == "back_to_channels":
            # Restart channels command
            await query.delete_message()
            # Simulate channels command
            from telegram import Message
            fake_update = Update(
                update_id=update.update_id,
                message=Message(
                    message_id=0,
                    date=update.callback_query.message.date,
                    chat=update.effective_chat,
                    from_user=update.effective_user
                )
            )
            await channels_command(fake_update, context)

        elif callback_data == "start_submission":
            await query.edit_message_text(
                "📝 برای ارسال متن برای بررسی از دستور /submit استفاده کنید."
            )

        elif callback_data == "upgrade_account":
            await query.edit_message_text(
                "💎 برای اطلاعات ارتقاء اکانت از دستور /upgrade استفاده کنید."
            )

        elif callback_data == "view_full_status":
            # Show full user status
            from handlers.stats_handlers import show_user_stats
            await show_user_stats(update, context)

        else:
            await query.answer("عملیات نامشخص")

    except Exception as e:
        logger.error(f"Error in handle_common_callbacks: {e}")
        await update.callback_query.answer("خطا در پردازش درخواست")


def register_channel_handlers(application) -> None:
    """
    Register channel-related handlers with the application.

    Args:
        application: Telegram Application instance
    """
    try:
        # Command handlers
        application.add_handler(CommandHandler("channels", channels_command))

        # Callback query handlers
        application.add_handler(CallbackQueryHandler(
            handle_channel_verification_callback,
            pattern="^(verify_all_channels|verify_channel:|view_limit_status|cancel_channel_operation).*"
        ))

        application.add_handler(CallbackQueryHandler(
            handle_common_callbacks,
            pattern="^(back_to_channels|start_submission|upgrade_account|view_full_status)$"
        ))

        logger.info("✅ Channel handlers registered successfully")

    except Exception as e:
        logger.error(f"❌ Failed to register channel handlers: {e}")
        raise