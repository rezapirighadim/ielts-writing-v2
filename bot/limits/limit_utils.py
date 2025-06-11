"""
Utility functions for limit management.
"""

import logging
from typing import Dict, Any, Optional
from telegram import Update
from .limit_manager import limit_manager
from .limit_exceptions import LimitExceededException

logger = logging.getLogger(__name__)


def check_user_can_submit_from_update(update: Update) -> tuple[bool, str]:
    """
    Check if user can submit from Telegram update.

    Args:
        update: Telegram update object

    Returns:
        tuple: (can_submit: bool, message: str)
    """
    try:
        if not update.effective_user:
            return False, "کاربر یافت نشد"

        telegram_id = update.effective_user.id
        return limit_manager.can_user_submit(telegram_id)

    except Exception as e:
        logger.error(f"Error checking user submission from update: {e}")
        return False, "خطا در بررسی محدودیت"


def process_submission_from_update(update: Update) -> tuple[bool, Dict[str, Any]]:
    """
    Process submission request from Telegram update.

    Args:
        update: Telegram update object

    Returns:
        tuple: (success: bool, info: dict)
    """
    try:
        if not update.effective_user:
            return False, {"error": "user_not_found", "message": "کاربر یافت نشد"}

        telegram_id = update.effective_user.id
        return limit_manager.process_submission_request(telegram_id)

    except Exception as e:
        logger.error(f"Error processing submission from update: {e}")
        return False, {"error": "system_error", "message": "خطای سیستم"}


def get_user_limit_info_from_update(update: Update) -> Dict[str, Any]:
    """
    Get user limit information from Telegram update.

    Args:
        update: Telegram update object

    Returns:
        dict: User limit information
    """
    try:
        if not update.effective_user:
            return {"error": "کاربر یافت نشد"}

        telegram_id = update.effective_user.id
        return limit_manager.get_user_limit_summary(telegram_id)

    except Exception as e:
        logger.error(f"Error getting user limit info from update: {e}")
        return {"error": str(e)}


def format_limit_message(limit_info: Dict[str, Any]) -> str:
    """
    Format limit information into a Persian message.

    Args:
        limit_info: Limit information dictionary

    Returns:
        str: Formatted Persian message
    """
    try:
        if 'error' in limit_info:
            return f"خطا در دریافت اطلاعات محدودیت: {limit_info['error']}"

        # Basic information
        current_usage = limit_info.get('current_usage', 0)
        monthly_limit = limit_info.get('monthly_limit', 0)
        bonus_requests = limit_info.get('bonus_requests', 0)
        available = limit_info.get('available_submissions', 0)
        is_premium = limit_info.get('is_premium', False)
        usage_percentage = limit_info.get('usage_percentage', 0)

        # Subscription type
        subscription_text = "پریمیوم" if is_premium else "رایگان"

        # Progress bar
        progress_bar = limit_info.get('progress_bar', '')

        # Usage status
        usage_label = limit_info.get('usage_label', 'عادی')

        # Reset date
        reset_date = limit_info.get('reset_date_formatted', 'نامشخص')
        days_until_reset = limit_info.get('days_until_reset', 0)

        message = f"""📊 وضعیت محدودیت شما

🔸 نوع اشتراک: {subscription_text}
🔸 استفاده ماهانه: {current_usage}/{monthly_limit}
🔸 درخواست‌های اضافی: {bonus_requests}
🔸 مجموع در دسترس: {available}

📈 درصد استفاده: {usage_percentage:.1f}% ({usage_label})
{progress_bar}

📅 تاریخ بازنشانی: {reset_date}
⏰ روزهای باقی‌مانده: {days_until_reset}

💡 وضعیت: {'✅ آماده دریافت متن' if available > 0 else '❌ محدودیت تمام شده'}"""

        # Add upgrade suggestion for free users near limit
        if not is_premium and usage_percentage > 70:
            message += "\n\n💎 برای دسترسی بیشتر، اکانت خود را ارتقاء دهید: /upgrade"

        # Add channel suggestion if no bonus requests
        if bonus_requests == 0:
            message += "\n\n📢 برای درخواست رایگان اضافی، در کانال‌ها عضو شوید: /channels"

        return message

    except Exception as e:
        logger.error(f"Error formatting limit message: {e}")
        return "خطا در نمایش اطلاعات محدودیت"


def format_limit_exceeded_message(limit_info: Dict[str, Any]) -> str:
    """
    Format limit exceeded message.

    Args:
        limit_info: Limit information dictionary

    Returns:
        str: Formatted exceeded limit message
    """
    try:
        current_usage = limit_info.get('current_usage', 0)
        monthly_limit = limit_info.get('monthly_limit', 0)
        bonus_requests = limit_info.get('bonus_requests', 0)
        is_premium = limit_info.get('is_premium', False)
        reset_date = limit_info.get('reset_date_formatted', 'نامشخص')

        message = f"""📊 محدودیت ماهانه تمام شده است

🔸 استفاده شده: {current_usage}/{monthly_limit}"""

        if bonus_requests > 0:
            message += f"\n🔸 درخواست‌های اضافی: {bonus_requests} (استفاده شده)"

        message += f"\n📅 بازنشانی در: {reset_date}"

        message += "\n\n💡 راه‌های دریافت درخواست بیشتر:"

        if not is_premium:
            message += "\n💎 ارتقاء به پریمیوم: /upgrade"

        message += "\n📢 عضویت در کانال‌ها: /channels"

        return message

    except Exception as e:
        logger.error(f"Error formatting limit exceeded message: {e}")
        return "محدودیت ماهانه تمام شده است. لطفاً ماه آینده مراجعه کنید."


def check_and_handle_limit_exception(func):
    """
    Decorator to handle limit exceptions in handler functions.

    Python Concept: This is a decorator that wraps functions to
    automatically handle LimitExceededException.
    """

    async def wrapper(update, context, *args, **kwargs):
        try:
            return await func(update, context, *args, **kwargs)
        except LimitExceededException as e:
            # Get user limit info for detailed message
            limit_info = get_user_limit_info_from_update(update)
            message = format_limit_exceeded_message(limit_info)
            await update.message.reply_text(message)
            return False
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            await update.message.reply_text("خطای غیرمنتظره در سیستم")
            return False

    return wrapper


def get_limit_warning_threshold() -> float:
    """
    Get the usage percentage threshold for warnings.

    Returns:
        float: Warning threshold percentage
    """
    return 80.0


def should_show_limit_warning(usage_percentage: float) -> bool:
    """
    Check if limit warning should be shown.

    Args:
        usage_percentage: Current usage percentage

    Returns:
        bool: True if warning should be shown
    """
    return usage_percentage >= get_limit_warning_threshold()


def format_bonus_grant_message(channel_title: str, bonus_amount: int,
                               total_bonus: int, available: int) -> str:
    """
    Format bonus grant message for channel membership.

    Args:
        channel_title: Channel title
        bonus_amount: Bonus amount granted
        total_bonus: Total bonus requests
        available: Total available submissions

    Returns:
        str: Formatted bonus message
    """
    return f"""🎉 تبریک!

با عضویت در کانال "{channel_title}" شما {bonus_amount} درخواست رایگان اضافی دریافت کردید!

📊 وضعیت جدید:
🔸 درخواست‌های اضافی: {total_bonus}
🔸 مجموع درخواست‌های موجود: {available}

💡 اکنون می‌توانید متن خود را برای بررسی ارسال کنید: /submit"""