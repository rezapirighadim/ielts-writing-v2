"""
User registration and management handlers.
"""

import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from shared.database import get_db_session
from shared.models.user import User
from shared.models.system_log import SystemLog
from shared.constants import SubscriptionType
from messages.persian_messages import PersianMessages

logger = logging.getLogger(__name__)


async def ensure_user_exists(telegram_user, session) -> User:
    """
    Ensure user exists in database, create if not exists.

    Args:
        telegram_user: Telegram user object from update
        session: Database session

    Returns:
        User: User object from database
    """
    telegram_id = telegram_user.id
    username = telegram_user.username
    first_name = telegram_user.first_name
    last_name = telegram_user.last_name

    # Check if user exists
    user = session.query(User).filter_by(telegram_id=telegram_id).first()

    if user:
        # Update user information and activity
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.update_activity()

        # Reset monthly usage if needed
        reset_occurred = user.reset_monthly_usage_if_needed()
        if reset_occurred:
            logger.info(f"Monthly usage reset for user {telegram_id}")

        return user
    else:
        # Create new user
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            subscription_type=SubscriptionType.FREE,
            registration_date=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            monthly_submissions=0,
            total_submissions=0,
            bonus_requests=0,
            is_active=True
        )

        session.add(new_user)
        session.flush()  # Get the user ID without committing

        # Log new user registration
        log_entry = SystemLog.create_log(
            level="INFO",
            message=f"New user registered: {telegram_id} (@{username}) - {first_name} {last_name}",
            module="user_handler",
            user_id=new_user.id,
            telegram_id=telegram_id
        )
        session.add(log_entry)

        logger.info(f"New user registered: {telegram_id} (@{username})")
        return new_user


async def get_user_from_update(update: Update) -> tuple[User, bool]:
    """
    Get or create user from Telegram update.

    Args:
        update: Telegram update object

    Returns:
        tuple: (User object, is_new_user boolean)
    """
    telegram_user = update.effective_user

    with get_db_session() as session:
        # Check if user exists before creating
        existing_user = session.query(User).filter_by(telegram_id=telegram_user.id).first()
        is_new_user = existing_user is None

        user = await ensure_user_exists(telegram_user, session)

        # Log user activity
        activity_log = SystemLog.create_log(
            level="INFO",
            message=f"User activity: {telegram_user.id} - {'new registration' if is_new_user else 'existing user'}",
            module="user_handler",
            user_id=user.id,
            telegram_id=telegram_user.id
        )
        session.add(activity_log)

        return user, is_new_user


def get_user_status_summary(user: User) -> dict:
    """
    Get comprehensive user status summary.

    Args:
        user: User object

    Returns:
        dict: User status information
    """
    return {
        'user_id': user.id,
        'telegram_id': user.telegram_id,
        'username': user.username,
        'display_name': user.display_name,
        'subscription_type': user.subscription_type.value,
        'is_premium': user.is_premium,
        'monthly_submissions': user.monthly_submissions,
        'monthly_limit': user.monthly_limit,
        'total_submissions': user.total_submissions,
        'bonus_requests': user.bonus_requests,
        'available_submissions': user.available_submissions,
        'can_submit': user.can_submit(),
        'registration_date': user.registration_date,
        'last_activity': user.last_activity,
        'is_active': user.is_active
    }


async def handle_user_registration_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> User:
    """
    Handle complete user registration flow.

    Args:
        update: Telegram update
        context: Bot context

    Returns:
        User: Registered user object
    """
    try:
        user, is_new_user = await get_user_from_update(update)

        if is_new_user:
            # Send welcome message for new users
            await update.message.reply_text(PersianMessages.START_NEW_USER)

            # Log successful registration
            logger.info(f"User registration completed: {user.telegram_id}")

        else:
            # Send returning user message
            user_data = get_user_status_summary(user)
            welcome_message = PersianMessages.format_welcome_returning_user(user_data)
            await update.message.reply_text(welcome_message)

            logger.info(f"Returning user greeted: {user.telegram_id}")

        return user

    except Exception as e:
        logger.error(f"Error in user registration flow: {e}")
        await update.message.reply_text(PersianMessages.ERROR_GENERAL)
        raise


async def check_user_submission_eligibility(user: User) -> tuple[bool, str]:
    """
    Check if user can submit a new writing sample.

    Args:
        user: User object

    Returns:
        tuple: (can_submit: bool, message: str)
    """
    try:
        # Refresh user data to get latest limits
        with get_db_session() as session:
            # Get fresh user data
            fresh_user = session.query(User).filter_by(id=user.id).first()
            if not fresh_user:
                return False, PersianMessages.ERROR_GENERAL

            # Check if monthly reset is needed
            reset_occurred = fresh_user.reset_monthly_usage_if_needed()
            if reset_occurred:
                logger.info(f"Monthly usage reset during eligibility check for user {fresh_user.telegram_id}")

            # Check submission eligibility
            if fresh_user.can_submit():
                available = fresh_user.available_submissions
                return True, f"✅ شما {available} درخواست باقی‌مانده دارید"
            else:
                # Generate limit reached message
                user_data = get_user_status_summary(fresh_user)
                limit_message = PersianMessages.format_monthly_limit_reached(user_data)
                return False, limit_message

    except Exception as e:
        logger.error(f"Error checking user submission eligibility: {e}")
        return False, PersianMessages.ERROR_GENERAL


async def update_user_info(telegram_user, session) -> User:
    """
    Update user information from Telegram data.

    Args:
        telegram_user: Telegram user object
        session: Database session

    Returns:
        User: Updated user object
    """
    user = session.query(User).filter_by(telegram_id=telegram_user.id).first()

    if user:
        # Update user information
        old_username = user.username
        old_first_name = user.first_name
        old_last_name = user.last_name

        user.username = telegram_user.username
        user.first_name = telegram_user.first_name
        user.last_name = telegram_user.last_name
        user.update_activity()

        # Log changes if any
        changes = []
        if old_username != user.username:
            changes.append(f"username: {old_username} -> {user.username}")
        if old_first_name != user.first_name:
            changes.append(f"first_name: {old_first_name} -> {user.first_name}")
        if old_last_name != user.last_name:
            changes.append(f"last_name: {old_last_name} -> {user.last_name}")

        if changes:
            log_entry = SystemLog.create_log(
                level="INFO",
                message=f"User info updated: {telegram_user.id} - {', '.join(changes)}",
                module="user_handler",
                user_id=user.id,
                telegram_id=telegram_user.id
            )
            session.add(log_entry)
            logger.info(f"User info updated for {telegram_user.id}: {', '.join(changes)}")

    return user


def format_user_statistics(user: User) -> str:
    """
    Format user statistics for display.

    Args:
        user: User object

    Returns:
        str: Formatted statistics text
    """
    try:
        # Calculate percentage of monthly limit used
        if user.monthly_limit > 0:
            usage_percentage = (user.monthly_submissions / user.monthly_limit) * 100
        else:
            usage_percentage = 0

        # Format registration date
        reg_date = "نامشخص"
        if user.registration_date:
            reg_date = user.registration_date.strftime('%Y/%m/%d')

        # Format last activity
        last_activity = "نامشخص"
        if user.last_activity:
            last_activity = user.last_activity.strftime('%Y/%m/%d %H:%M')

        # Create progress bar for monthly usage
        from messages.message_formatter import create_progress_bar
        progress_bar = create_progress_bar(user.monthly_submissions, user.monthly_limit, 10)

        stats_text = f"""📊 آمار کاربر {user.display_name}

👤 اطلاعات حساب:
- شناسه کاربری: @{user.username or 'ندارد'}
- نوع اشتراک: {'پریمیوم' if user.is_premium else 'رایگان'}
- تاریخ عضویت: {reg_date}
- آخرین فعالیت: {last_activity}

📈 آمار استفاده:
- کل ارسال‌ها: {user.total_submissions}
- ارسال‌های ماه جاری: {user.monthly_submissions}/{user.monthly_limit}
- درصد استفاده ماهانه: {usage_percentage:.1f}%
- درخواست‌های اضافی: {user.bonus_requests}
- مجموع درخواست‌های موجود: {user.available_submissions}

📊 نمودار استفاده ماهانه:
{progress_bar} {user.monthly_submissions}/{user.monthly_limit}

💡 وضعیت: {'آماده دریافت متن' if user.can_submit() else 'محدودیت ماهانه پر شده'}"""

        return stats_text

    except Exception as e:
        logger.error(f"Error formatting user statistics: {e}")
        return "خطا در نمایش آمار"


async def log_user_action(user: User, action: str, details: str = None):
    """
    Log user action to database.

    Args:
        user: User object
        action: Action description
        details: Additional details (optional)
    """
    try:
        with get_db_session() as session:
            message = f"User action: {action}"
            if details:
                message += f" - {details}"

            log_entry = SystemLog.create_log(
                level="INFO",
                message=message,
                module="user_handler",
                user_id=user.id,
                telegram_id=user.telegram_id
            )
            session.add(log_entry)

    except Exception as e:
        logger.error(f"Error logging user action: {e}")