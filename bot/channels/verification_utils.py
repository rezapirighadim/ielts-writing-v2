"""
Utility functions for channel membership verification.
"""

import logging
from typing import Dict, Any, Optional, List
from telegram import Update, Bot
from .channel_manager import ChannelManager
from database.user_operations import UserOperations

logger = logging.getLogger(__name__)

async def verify_user_membership(update: Update, bot: Bot, channel_username: str = None) -> Dict[str, Any]:
    """
    Verify user membership from Telegram update.

    Args:
        update: Telegram update object
        bot: Telegram bot instance
        channel_username: Specific channel to check (optional, checks all if None)

    Returns:
        dict: Verification results
    """
    try:
        if not update.effective_user:
            return {
                "success": False,
                "error": "user_not_found",
                "message": "کاربر یافت نشد"
            }

        telegram_id = update.effective_user.id

        # Get user from database
        user = UserOperations.get_user_by_telegram_id(telegram_id)
        if not user:
            return {
                "success": False,
                "error": "user_not_registered",
                "message": "لطفاً ابتدا از دستور /start استفاده کنید"
            }

        # Create channel manager
        channel_manager = ChannelManager(bot)

        # Check specific channel or all channels
        if channel_username:
            # Remove @ if present
            clean_username = channel_username.lstrip('@')
            result = await channel_manager.check_single_channel_membership(
                telegram_id=telegram_id,
                channel_username=clean_username,
                user_id=user.id
            )
        else:
            # Check all channels
            result = await channel_manager.verify_and_grant_bonuses(
                telegram_id=telegram_id,
                user_id=user.id
            )

        return result

    except Exception as e:
        logger.error(f"Error in verify_user_membership: {e}")
        return {
            "success": False,
            "error": "system_error",
            "message": "خطا در بررسی عضویت"
        }

def get_channel_bonus_info(user_id: int) -> Dict[str, Any]:
    """
    Get information about channels available for bonus requests.

    Args:
        user_id: Database user ID

    Returns:
        dict: Channel bonus information
    """
    try:
        from database.channel_operations import ChannelOperations

        # Get channels available for bonus
        available_channels = ChannelOperations.get_channels_for_user_bonus_check(user_id)

        # Get current memberships
        current_memberships = ChannelOperations.get_user_memberships(user_id)

        # Calculate statistics
        total_channels = len(available_channels)
        member_channels = len([ch for ch in available_channels if ch.get('is_member', False)])
        bonus_eligible_channels = len([ch for ch in available_channels if ch.get('can_get_bonus', False)])
        total_potential_bonus = sum(
            ch.get('bonus_requests', 0) for ch in available_channels if ch.get('can_get_bonus', False)
        )

        return {
            "success": True,
            "total_channels": total_channels,
            "member_channels": member_channels,
            "bonus_eligible_channels": bonus_eligible_channels,
            "total_potential_bonus": total_potential_bonus,
            "available_channels": available_channels,
            "current_memberships": current_memberships
        }

    except Exception as e:
        logger.error(f"Error getting channel bonus info for user {user_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_channels": 0,
            "member_channels": 0,
            "bonus_eligible_channels": 0,
            "total_potential_bonus": 0,
            "available_channels": [],
            "current_memberships": []
        }

def format_channel_list_message(channel_info: Dict[str, Any]) -> str:
    """
    Format channel list for display to users.

    Args:
        channel_info: Channel information from get_channel_bonus_info

    Returns:
        str: Formatted Persian message
    """
    try:
        if not channel_info.get("success", False):
            return "خطا در دریافت اطلاعات کانال‌ها"

        available_channels = channel_info.get("available_channels", [])
        total_potential_bonus = channel_info.get("total_potential_bonus", 0)

        if not available_channels:
            return "در حال حاضر کانالی برای دریافت درخواست رایگان موجود نیست."

        message = "📢 کانال‌های موجود برای دریافت درخواست رایگان:\n\n"

        for i, channel in enumerate(available_channels, 1):
            channel_title = channel.get('channel_title', 'نامشخص')
            channel_username = channel.get('channel_username', '')
            bonus_amount = channel.get('bonus_requests', 0)
            is_member = channel.get('is_member', False)
            can_get_bonus = channel.get('can_get_bonus', False)

            status_emoji = "✅" if is_member else "❌"
            bonus_status = ""

            if is_member:
                if can_get_bonus:
                    bonus_status = f" 🎁 {bonus_amount} درخواست رایگان"
                else:
                    bonus_status = " ✓ قبلاً دریافت شده"
            else:
                bonus_status = f" 🎁 {bonus_amount} درخواست رایگان"

            channel_url = f"https://t.me/{channel_username}"
            message += f"{i}. {status_emoji} [{channel_title}]({channel_url}){bonus_status}\n"

        message += f"\n💰 مجموع درخواست‌های رایگان قابل دریافت: {total_potential_bonus}"

        if total_potential_bonus > 0:
            message += "\n\n📝 نحوه دریافت:\n"
            message += "1️⃣ در کانال‌های بالا عضو شوید\n"
            message += "2️⃣ روی دکمه 'بررسی عضویت' کلیک کنید\n"
            message += "3️⃣ درخواست‌های رایگان به حساب شما افزوده می‌شود"

        return message

    except Exception as e:
        logger.error(f"Error formatting channel list message: {e}")
        return "خطا در نمایش لیست کانال‌ها"

def format_membership_verification_message(verification_result: Dict[str, Any]) -> str:
    """
    Format membership verification result message.

    Args:
        verification_result: Result from verify_user_membership

    Returns:
        str: Formatted Persian message
    """
    try:
        if not verification_result.get("success", False):
            error_message = verification_result.get("message", "خطا در بررسی عضویت")
            return f"❌ {error_message}"

        # Check if this is a single channel result or multiple channels
        if "channel_username" in verification_result:
            # Single channel result
            return verification_result.get("message", "بررسی عضویت انجام شد")
        else:
            # Multiple channels result
            total_bonuses = verification_result.get("total_bonuses_granted", 0)
            message = verification_result.get("message", "")
            available_submissions = verification_result.get("available_submissions", 0)

            if total_bonuses > 0:
                message += f"\n\n📊 مجموع درخواست‌های موجود: {available_submissions}"
                message += "\n\n💡 اکنون می‌توانید متن خود را برای بررسی ارسال کنید: /submit"

            return message

    except Exception as e:
        logger.error(f"Error formatting verification message: {e}")
        return "بررسی عضویت انجام شد"

async def setup_channel_verification_for_bot(bot: Bot, channel_configs: List[Dict[str, Any]]) -> bool:
    """
    Setup channels for verification (admin function).

    Args:
        bot: Telegram bot instance
        channel_configs: List of channel configurations

    Returns:
        bool: True if setup successful
    """
    try:
        success_count = 0

        for config in channel_configs:
            try:
                channel_username = config.get('username', '').lstrip('@')
                channel_title = config.get('title', '')
                bonus_requests = config.get('bonus_requests', 5)
                description = config.get('description', '')

                # Get channel info from Telegram
                try:
                    chat = await bot.get_chat(f"@{channel_username}")
                    channel_id = chat.id
                    if not channel_title:
                        channel_title = chat.title or channel_username
                except Exception as e:
                    logger.warning(f"Could not get channel info for @{channel_username}: {e}")
                    channel_id = 0  # Will need to be updated manually

                # Create channel in database
                from database.channel_operations import ChannelOperations
                channel = ChannelOperations.create_channel(
                    channel_username=channel_username,
                    channel_title=channel_title,
                    channel_id=channel_id,
                    bonus_requests=bonus_requests,
                    description=description
                )

                if channel:
                    success_count += 1
                    logger.info(f"Setup channel: @{channel_username}")

            except Exception as e:
                logger.error(f"Error setting up channel {config}: {e}")

        logger.info(f"Channel setup completed: {success_count}/{len(channel_configs)} successful")
        return success_count > 0

    except Exception as e:
        logger.error(f"Error in setup_channel_verification_for_bot: {e}")
        return False

def create_membership_check_buttons():
    """
    Create inline keyboard buttons for membership verification.

    Returns:
        InlineKeyboardMarkup: Keyboard with verification buttons
    """
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        buttons = [
            [InlineKeyboardButton("🔍 بررسی عضویت در تمام کانال‌ها", callback_data="check_all_channels")],
            [InlineKeyboardButton("📊 مشاهده وضعیت درخواست‌ها", callback_data="view_limit_status")],
            [InlineKeyboardButton("❌ انصراف", callback_data="cancel_operation")]
        ]

        return InlineKeyboardMarkup(buttons)

    except Exception as e:
        logger.error(f"Error creating membership check buttons: {e}")
        return None

def create_channel_specific_buttons(available_channels: List[Dict[str, Any]]):
    """
    Create inline keyboard buttons for specific channel verification.

    Args:
        available_channels: List of available channels

    Returns:
        InlineKeyboardMarkup: Keyboard with channel-specific buttons
    """
    try:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        buttons = []

        # Add button for each channel (limit to 5 to avoid message size issues)
        for channel in available_channels[:5]:
            channel_title = channel.get('channel_title', 'نامشخص')
            channel_username = channel.get('channel_username', '')
            can_get_bonus = channel.get('can_get_bonus', False)

            button_text = f"🔍 {channel_title}"
            if can_get_bonus:
                bonus_amount = channel.get('bonus_requests', 0)
                button_text += f" (+{bonus_amount})"

            callback_data = f"check_channel:{channel_username}"
            buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

        # Add general options
        buttons.append([InlineKeyboardButton("🔍 بررسی همه کانال‌ها", callback_data="check_all_channels")])
        buttons.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel_operation")])

        return InlineKeyboardMarkup(buttons)

    except Exception as e:
        logger.error(f"Error creating channel specific buttons: {e}")
        return None

def extract_channel_username_from_callback(callback_data: str) -> Optional[str]:
    """
    Extract channel username from callback data.

    Args:
        callback_data: Callback data string

    Returns:
        str: Channel username or None
    """
    try:
        if callback_data.startswith("check_channel:"):
            return callback_data.split(":", 1)[1]
        return None
    except Exception as e:
        logger.error(f"Error extracting channel username from callback: {e}")
        return None

def get_verification_status_summary(verification_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get summary of verification results.

    Args:
        verification_results: List of verification results

    Returns:
        dict: Summary statistics
    """
    try:
        total_channels = len(verification_results)
        member_channels = len([r for r in verification_results if r.get('is_member', False)])
        bonus_eligible = len([r for r in verification_results if r.get('bonus_eligible', False)])
        total_bonus = sum(r.get('bonus_amount', 0) for r in verification_results if r.get('bonus_eligible', False))

        return {
            "total_channels": total_channels,
            "member_channels": member_channels,
            "bonus_eligible_channels": bonus_eligible,
            "total_potential_bonus": total_bonus,
            "membership_rate": (member_channels / total_channels * 100) if total_channels > 0 else 0
        }

    except Exception as e:
        logger.error(f"Error getting verification status summary: {e}")
        return {
            "total_channels": 0,
            "member_channels": 0,
            "bonus_eligible_channels": 0,
            "total_potential_bonus": 0,
            "membership_rate": 0
        }

async def verify_user_in_channel_by_callback(update: Update, bot: Bot, callback_data: str) -> Dict[str, Any]:
    """
    Verify user membership based on callback data.

    Args:
        update: Telegram update object
        bot: Telegram bot instance
        callback_data: Callback data from inline button

    Returns:
        dict: Verification result
    """
    try:
        if callback_data == "check_all_channels":
            # Verify all channels
            return await verify_user_membership(update, bot)
        elif callback_data.startswith("check_channel:"):
            # Verify specific channel
            channel_username = extract_channel_username_from_callback(callback_data)
            if channel_username:
                return await verify_user_membership(update, bot, channel_username)
            else:
                return {
                    "success": False,
                    "error": "invalid_callback",
                    "message": "داده نامعتبر"
                }
        else:
            return {
                "success": False,
                "error": "unknown_callback",
                "message": "عملیات نامشخص"
            }

    except Exception as e:
        logger.error(f"Error in verify_user_in_channel_by_callback: {e}")
        return {
            "success": False,
            "error": "system_error",
            "message": "خطا در بررسی عضویت"
        }