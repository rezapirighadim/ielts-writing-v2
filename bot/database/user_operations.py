"""
Database operations specific to user management.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from shared.database import get_db_session
from shared.models.user import User
from shared.models.system_log import SystemLog
from shared.constants import SubscriptionType

logger = logging.getLogger(__name__)


class UserOperations:
    """
    Database operations class for user management.

    Python Concept: This class encapsulates all user-related database operations
    providing a clean interface for handlers to interact with user data.
    """

    @staticmethod
    def create_user(telegram_id: int, username: str = None, first_name: str = None,
                    last_name: str = None) -> Optional[User]:
        """
        Create a new user in the database.

        Args:
            telegram_id: Telegram user ID
            username: Telegram username (optional)
            first_name: User's first name (optional)
            last_name: User's last name (optional)

        Returns:
            User object if successful, None otherwise
        """
        try:
            with get_db_session() as session:
                # Check if user already exists
                existing_user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if existing_user:
                    logger.warning(f"Attempted to create existing user: {telegram_id}")
                    return existing_user

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
                session.flush()  # Get the ID

                # Log user creation
                log_entry = SystemLog.create_log(
                    level="INFO",
                    message=f"User created: {telegram_id} (@{username})",
                    module="user_operations",
                    user_id=new_user.id,
                    telegram_id=telegram_id
                )
                session.add(log_entry)

                logger.info(f"User created successfully: {telegram_id}")
                return new_user

        except Exception as e:
            logger.error(f"Error creating user {telegram_id}: {e}")
            return None

    @staticmethod
    def get_user_by_telegram_id(telegram_id: int) -> Optional[User]:
        """
        Get user by Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User object if found, None otherwise
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

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[User]:
        """
        Get user by database ID.

        Args:
            user_id: User database ID

        Returns:
            User object if found, None otherwise
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(id=user_id).first()
                if user:
                    session.expunge(user)
                return user
        except Exception as e:
            logger.error(f"Error getting user by id {user_id}: {e}")
            return None

    @staticmethod
    def update_user_info(telegram_id: int, username: str = None, first_name: str = None,
                         last_name: str = None) -> bool:
        """
        Update user information.

        Args:
            telegram_id: Telegram user ID
            username: New username (optional)
            first_name: New first name (optional)
            last_name: New last name (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if not user:
                    logger.warning(f"User not found for update: {telegram_id}")
                    return False

                # Track changes
                changes = []
                if username is not None and user.username != username:
                    changes.append(f"username: {user.username} -> {username}")
                    user.username = username

                if first_name is not None and user.first_name != first_name:
                    changes.append(f"first_name: {user.first_name} -> {first_name}")
                    user.first_name = first_name

                if last_name is not None and user.last_name != last_name:
                    changes.append(f"last_name: {user.last_name} -> {last_name}")
                    user.last_name = last_name

                # Update activity
                user.update_activity()

                # Log changes if any
                if changes:
                    log_entry = SystemLog.create_log(
                        level="INFO",
                        message=f"User info updated: {', '.join(changes)}",
                        module="user_operations",
                        user_id=user.id,
                        telegram_id=telegram_id
                    )
                    session.add(log_entry)
                    logger.info(f"User info updated for {telegram_id}: {', '.join(changes)}")

                return True

        except Exception as e:
            logger.error(f"Error updating user info for {telegram_id}: {e}")
            return False

    @staticmethod
    def update_user_activity(telegram_id: int) -> bool:
        """
        Update user's last activity timestamp.

        Args:
            telegram_id: Telegram user ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    user.update_activity()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating user activity for {telegram_id}: {e}")
            return False

    @staticmethod
    def check_and_reset_monthly_usage(telegram_id: int) -> bool:
        """
        Check and reset monthly usage if needed.

        Args:
            telegram_id: Telegram user ID

        Returns:
            bool: True if reset occurred, False otherwise
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    reset_occurred = user.reset_monthly_usage_if_needed()
                    if reset_occurred:
                        log_entry = SystemLog.create_log(
                            level="INFO",
                            message="Monthly usage reset",
                            module="user_operations",
                            user_id=user.id,
                            telegram_id=telegram_id
                        )
                        session.add(log_entry)
                        logger.info(f"Monthly usage reset for user {telegram_id}")
                    return reset_occurred
                return False
        except Exception as e:
            logger.error(f"Error checking monthly reset for {telegram_id}: {e}")
            return False

    @staticmethod
    def increment_user_submissions(telegram_id: int) -> bool:
        """
        Increment user's submission counts.

        Args:
            telegram_id: Telegram user ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user and user.use_submission():
                    # Log the submission increment
                    log_entry = SystemLog.create_log(
                        level="INFO",
                        message=f"Submission incremented: monthly={user.monthly_submissions}, total={user.total_submissions}",
                        module="user_operations",
                        user_id=user.id,
                        telegram_id=telegram_id
                    )
                    session.add(log_entry)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error incrementing submissions for {telegram_id}: {e}")
            return False

    @staticmethod
    def add_bonus_requests(telegram_id: int, amount: int) -> int:
        """
        Add bonus requests to user account.

        Args:
            telegram_id: Telegram user ID
            amount: Number of bonus requests to add

        Returns:
            int: Number of bonus requests actually added
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    added = user.add_bonus_requests(amount)

                    # Log bonus addition
                    log_entry = SystemLog.create_log(
                        level="INFO",
                        message=f"Bonus requests added: {added} (requested: {amount}, new total: {user.bonus_requests})",
                        module="user_operations",
                        user_id=user.id,
                        telegram_id=telegram_id
                    )
                    session.add(log_entry)

                    logger.info(f"Added {added} bonus requests to user {telegram_id}")
                    return added
                return 0
        except Exception as e:
            logger.error(f"Error adding bonus requests to {telegram_id}: {e}")
            return 0

    @staticmethod
    def get_user_stats(telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive user statistics.

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: User statistics or None if user not found
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    return {
                        'user_id': user.id,
                        'telegram_id': user.telegram_id,
                        'username': user.username,
                        'display_name': user.display_name,
                        'full_name': user.full_name,
                        'subscription_type': user.subscription_type.value,
                        'is_premium': user.is_premium,
                        'registration_date': user.registration_date,
                        'last_activity': user.last_activity,
                        'monthly_submissions': user.monthly_submissions,
                        'monthly_limit': user.monthly_limit,
                        'total_submissions': user.total_submissions,
                        'bonus_requests': user.bonus_requests,
                        'available_submissions': user.available_submissions,
                        'can_submit': user.can_submit(),
                        'is_active': user.is_active
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting user stats for {telegram_id}: {e}")
            return None

    @staticmethod
    def upgrade_user_to_premium(telegram_id: int) -> bool:
        """
        Upgrade user to premium subscription.

        Args:
            telegram_id: Telegram user ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                user = session.query(User).filter_by(telegram_id=telegram_id).first()
                if user:
                    old_type = user.subscription_type
                    user.subscription_type = SubscriptionType.PREMIUM
                    user.update_activity()

                    # Log upgrade
                    log_entry = SystemLog.create_log(
                        level="INFO",
                        message=f"User upgraded to premium: {old_type.value} -> {user.subscription_type.value}",
                        module="user_operations",
                        user_id=user.id,
                        telegram_id=telegram_id
                    )
                    session.add(log_entry)

                    logger.info(f"User {telegram_id} upgraded to premium")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error upgrading user {telegram_id} to premium: {e}")
            return False

    @staticmethod
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

                    # Log deactivation
                    log_entry = SystemLog.create_log(
                        level="WARNING",
                        message=f"User deactivated: {reason}",
                        module="user_operations",
                        user_id=user.id,
                        telegram_id=telegram_id
                    )
                    session.add(log_entry)

                    logger.warning(f"User {telegram_id} deactivated: {reason}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deactivating user {telegram_id}: {e}")
            return False

    @staticmethod
    def get_users_by_subscription_type(subscription_type: SubscriptionType,
                                       active_only: bool = True) -> List[User]:
        """
        Get users by subscription type.

        Args:
            subscription_type: Subscription type to filter by
            active_only: Whether to include only active users

        Returns:
            List of User objects
        """
        try:
            with get_db_session() as session:
                query = session.query(User).filter_by(subscription_type=subscription_type)

                if active_only:
                    query = query.filter_by(is_active=True)

                users = query.all()

                # Detach from session
                for user in users:
                    session.expunge(user)

                return users
        except Exception as e:
            logger.error(f"Error getting users by subscription type {subscription_type}: {e}")
            return []

    @staticmethod
    def get_recent_users(days: int = 7, limit: int = 100) -> List[User]:
        """
        Get recently active users.

        Args:
            days: Number of days to look back
            limit: Maximum number of users to return

        Returns:
            List of User objects
        """
        try:
            from datetime import timedelta

            with get_db_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)

                users = (
                    session.query(User)
                    .filter(User.last_activity >= cutoff_date)
                    .filter_by(is_active=True)
                    .order_by(User.last_activity.desc())
                    .limit(limit)
                    .all()
                )

                # Detach from session
                for user in users:
                    session.expunge(user)

                return users
        except Exception as e:
            logger.error(f"Error getting recent users: {e}")
            return []

    @staticmethod
    def get_user_count_statistics() -> Dict[str, int]:
        """
        Get user count statistics.

        Returns:
            dict: Statistics including total, active, premium users etc.
        """
        try:
            with get_db_session() as session:
                total_users = session.query(User).count()
                active_users = session.query(User).filter_by(is_active=True).count()
                premium_users = session.query(User).filter_by(
                    subscription_type=SubscriptionType.PREMIUM,
                    is_active=True
                ).count()
                free_users = session.query(User).filter_by(
                    subscription_type=SubscriptionType.FREE,
                    is_active=True
                ).count()

                # Users with submissions this month
                from datetime import date
                current_month_start = date.today().replace(day=1)

                active_submitters = session.query(User).filter(
                    User.monthly_submissions > 0,
                    User.last_submission_reset >= current_month_start,
                    User.is_active == True
                ).count()

                return {
                    'total_users': total_users,
                    'active_users': active_users,
                    'premium_users': premium_users,
                    'free_users': free_users,
                    'active_submitters': active_submitters
                }
        except Exception as e:
            logger.error(f"Error getting user count statistics: {e}")
            return {
                'total_users': 0,
                'active_users': 0,
                'premium_users': 0,
                'free_users': 0,
                'active_submitters': 0
            }