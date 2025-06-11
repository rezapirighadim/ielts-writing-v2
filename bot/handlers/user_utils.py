"""
User-related utility functions for handlers.
"""

import logging
from typing import Optional
from shared.database import get_db_session
from shared.models.user import User
from shared.models.system_log import SystemLog

logger = logging.getLogger(__name__)


def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
    """
    Get user by Telegram ID.

    Args:
        telegram_id: Telegram user ID

    Returns:
        User object or None if not found
    """
    try:
        with get_db_session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                # Detach from session to avoid lazy loading issues
                session.expunge(user)
            return user
    except Exception as e:
        logger.error(f"Error getting user by telegram_id {telegram_id}: {e}")
        return None


def increment_user_submissions(user_id: int) -> bool:
    """
    Increment user's submission counts.

    Args:
        user_id: User database ID

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if user and user.use_submission():
                # Log the submission usage
                log_entry = SystemLog.create_log(
                    level="INFO",
                    message=f"Submission count incremented: monthly={user.monthly_submissions}, total={user.total_submissions}",
                    module="user_utils",
                    user_id=user.id,
                    telegram_id=user.telegram_id
                )
                session.add(log_entry)
                return True
            return False
    except Exception as e:
        logger.error(f"Error incrementing submissions for user {user_id}: {e}")
        return False


def add_bonus_requests_to_user(user_id: int, amount: int) -> int:
    """
    Add bonus requests to user account.

    Args:
        user_id: User database ID
        amount: Number of bonus requests to add

    Returns:
        int: Number of bonus requests actually added
    """
    try:
        with get_db_session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                added = user.add_bonus_requests(amount)

                # Log the bonus addition
                log_entry = SystemLog.create_log(
                    level="INFO",
                    message=f"Bonus requests added: {added} (requested: {amount}, new total: {user.bonus_requests})",
                    module="user_utils",
                    user_id=user.id,
                    telegram_id=user.telegram_id
                )
                session.add(log_entry)

                return added
            return 0
    except Exception as e:
        logger.error(f"Error adding bonus requests to user {user_id}: {e}")
        return 0


def get_user_submission_history(user_id: int, limit: int = 10) -> list:
    """
    Get user's recent submission history.

    Args:
        user_id: User database ID
        limit: Maximum number of submissions to return

    Returns:
        list: List of submission dictionaries
    """
    try:
        with get_db_session() as session:
            from shared.models.submission import Submission

            submissions = (
                session.query(Submission)
                .filter_by(user_id=user_id)
                .order_by(Submission.submission_date.desc())
                .limit(limit)
                .all()
            )

            return [submission.to_dict() for submission in submissions]

    except Exception as e:
        logger.error(f"Error getting submission history for user {user_id}: {e}")
        return []


def check_user_active_status(telegram_id: int) -> bool:
    """
    Check if user account is active.

    Args:
        telegram_id: Telegram user ID

    Returns:
        bool: True if user is active, False otherwise
    """
    try:
        user = get_user_by_telegram_id(telegram_id)
        return user.is_active if user else False
    except Exception as e:
        logger.error(f"Error checking user active status for {telegram_id}: {e}")
        return False


def deactivate_user(telegram_id: int, reason: str = "Manual deactivation") -> bool:
    """
    Deactivate user account.

    Args:
        telegram_id: Telegram user ID
        reason: Reason for deactivation

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.is_active = False

                # Log the deactivation
                log_entry = SystemLog.create_log(
                    level="WARNING",
                    message=f"User deactivated: {reason}",
                    module="user_utils",
                    user_id=user.id,
                    telegram_id=telegram_id
                )
                session.add(log_entry)

                logger.info(f"User {telegram_id} deactivated: {reason}")
                return True
            return False
    except Exception as e:
        logger.error(f"Error deactivating user {telegram_id}: {e}")
        return False


def reactivate_user(telegram_id: int, reason: str = "Manual reactivation") -> bool:
    """
    Reactivate user account.

    Args:
        telegram_id: Telegram user ID
        reason: Reason for reactivation

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with get_db_session() as session:
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.is_active = True
                user.update_activity()

                # Log the reactivation
                log_entry = SystemLog.create_log(
                    level="INFO",
                    message=f"User reactivated: {reason}",
                    module="user_utils",
                    user_id=user.id,
                    telegram_id=telegram_id
                )
                session.add(log_entry)

                logger.info(f"User {telegram_id} reactivated: {reason}")
                return True
            return False
    except Exception as e:
        logger.error(f"Error reactivating user {telegram_id}: {e}")
        return False