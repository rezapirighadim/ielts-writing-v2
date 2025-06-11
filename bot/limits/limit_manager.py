"""
High-level limit management for the bot system.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, date, timedelta
from shared.database import get_db_session
from shared.models.system_config import SystemConfig
from shared.constants import SubscriptionType
from database.user_operations import UserOperations
from .usage_limiter import usage_limiter, LimitCheckResult

logger = logging.getLogger(__name__)


class LimitManager:
    """
    High-level manager for all limit-related operations.

    Python Concept: This class provides a facade pattern that
    simplifies complex limit operations for other parts of the system.
    """

    def __init__(self):
        self._config_cache = {}
        self._config_cache_ttl = 600  # 10 minutes

    def can_user_submit(self, telegram_id: int) -> tuple[bool, str]:
        """
        Simple check if user can submit.

        Args:
            telegram_id: Telegram user ID

        Returns:
            tuple: (can_submit: bool, message: str)
        """
        try:
            result = usage_limiter.check_submission_limit(telegram_id)
            return result.can_proceed, result.message
        except Exception as e:
            logger.error(f"Error checking if user can submit: {e}")
            return False, "خطا در بررسی محدودیت"

    def process_submission_request(self, telegram_id: int) -> tuple[bool, Dict[str, Any]]:
        """
        Process a submission request with full limit checking.

        Args:
            telegram_id: Telegram user ID

        Returns:
            tuple: (success: bool, info: dict)
        """
        try:
            # Check limits
            result = usage_limiter.check_submission_limit(telegram_id)

            if not result.can_proceed:
                return False, {
                    "error": "limit_exceeded",
                    "message": result.message,
                    "current_usage": result.current_usage,
                    "limit": result.limit,
                    "bonus_requests": result.bonus_requests,
                    "reset_date": result.reset_date.isoformat() if result.reset_date else None
                }

            # Consume submission
            consumed = usage_limiter.consume_submission(telegram_id)

            if consumed:
                # Get updated status
                updated_result = usage_limiter.check_submission_limit(telegram_id)

                return True, {
                    "success": True,
                    "message": "درخواست پذیرفته شد",
                    "remaining_submissions": updated_result.available_submissions,
                    "current_usage": updated_result.current_usage,
                    "limit": updated_result.limit
                }
            else:
                return False, {
                    "error": "consumption_failed",
                    "message": "خطا در ثبت درخواست"
                }

        except Exception as e:
            logger.error(f"Error processing submission request for {telegram_id}: {e}")
            return False, {
                "error": "system_error",
                "message": "خطای سیستم"
            }

    def grant_channel_bonus(self, telegram_id: int, channel_title: str, bonus_amount: int) -> tuple[
        bool, Dict[str, Any]]:
        """
        Grant bonus requests for channel membership.

        Args:
            telegram_id: Telegram user ID
            channel_title: Channel title for logging
            bonus_amount: Number of bonus requests to grant

        Returns:
            tuple: (success: bool, info: dict)
        """
        try:
            # Add bonus requests
            added = usage_limiter.add_bonus_requests(
                telegram_id=telegram_id,
                amount=bonus_amount,
                reason=f"Channel membership: {channel_title}"
            )

            if added > 0:
                # Get updated status
                status = usage_limiter.get_limit_status(telegram_id)

                return True, {
                    "success": True,
                    "bonus_added": added,
                    "total_bonus": status.get('bonus_requests', 0),
                    "available_submissions": status.get('available_submissions', 0),
                    "message": f"{added} درخواست رایگان اضافی دریافت کردید!"
                }
            else:
                return False, {
                    "error": "bonus_failed",
                    "message": "امکان اضافه کردن درخواست رایگان وجود ندارد"
                }

        except Exception as e:
            logger.error(f"Error granting channel bonus for {telegram_id}: {e}")
            return False, {
                "error": "system_error",
                "message": "خطا در اعطای درخواست رایگان"
            }

    def get_user_limit_summary(self, telegram_id: int) -> Dict[str, Any]:
        """
        Get comprehensive user limit summary.

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: Complete limit information
        """
        try:
            status = usage_limiter.get_limit_status(telegram_id)

            # Add formatted information
            if 'error' not in status:
                # Format dates
                if status.get('reset_date'):
                    reset_date = datetime.fromisoformat(status['reset_date']).date()
                    status['reset_date_formatted'] = reset_date.strftime('%Y/%m/%d')

                # Add progress indicators
                if status.get('monthly_limit', 0) > 0:
                    progress = (status.get('current_usage', 0) / status['monthly_limit']) * 10
                    status['progress_bar'] = '█' * int(progress) + '░' * (10 - int(progress))

                # Add status labels
                if status.get('usage_percentage', 0) >= 90:
                    status['usage_status'] = "critical"
                    status['usage_label'] = "بحرانی"
                elif status.get('usage_percentage', 0) >= 70:
                    status['usage_status'] = "warning"
                    status['usage_label'] = "هشدار"
                else:
                    status['usage_status'] = "normal"
                    status['usage_label'] = "عادی"

            return status

        except Exception as e:
            logger.error(f"Error getting user limit summary for {telegram_id}: {e}")
            return {"error": str(e)}

    def upgrade_user_subscription(self, telegram_id: int) -> tuple[bool, str]:
        """
        Upgrade user to premium subscription.

        Args:
            telegram_id: Telegram user ID

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            success = usage_limiter.upgrade_user_to_premium(telegram_id)

            if success:
                return True, "حساب شما با موفقیت به پریمیوم ارتقاء یافت!"
            else:
                return False, "خطا در ارتقاء حساب"

        except Exception as e:
            logger.error(f"Error upgrading user subscription for {telegram_id}: {e}")
            return False, "خطای سیستم در ارتقاء حساب"

    def get_system_limit_stats(self) -> Dict[str, Any]:
        """
        Get system-wide limit statistics.

        Returns:
            dict: System limit statistics
        """
        try:
            # Get user count statistics
            user_stats = UserOperations.get_user_count_statistics()

            # Get users near limit
            near_limit_users = usage_limiter.get_users_near_limit(80.0)

            # Get current limit configuration
            config = self._get_current_limits()

            return {
                "user_statistics": user_stats,
                "users_near_limit": len(near_limit_users),
                "current_limits": config,
                "cache_stats": usage_limiter.get_cache_stats(),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting system limit stats: {e}")
            return {"error": str(e)}

    def reset_user_monthly_usage(self, telegram_id: int) -> tuple[bool, str]:
        """
        Manually reset user's monthly usage (admin function).

        Args:
            telegram_id: Telegram user ID

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Force reset by updating database directly
            with get_db_session() as session:
                from shared.models.user import User
                user = session.query(User).filter_by(telegram_id=telegram_id).first()

                if user:
                    user.monthly_submissions = 0
                    user.last_submission_reset = date.today()

                    # Clear cache
                    usage_limiter._clear_cache(telegram_id)

                    logger.info(f"Manually reset monthly usage for user {telegram_id}")
                    return True, "استفاده ماهانه کاربر بازنشانی شد"
                else:
                    return False, "کاربر یافت نشد"

        except Exception as e:
            logger.error(f"Error resetting monthly usage for {telegram_id}: {e}")
            return False, "خطا در بازنشانی استفاده ماهانه"

    def bulk_reset_monthly_usage(self) -> Dict[str, int]:
        """
        Bulk reset monthly usage for all users (scheduled task).

        Returns:
            dict: Reset statistics
        """
        try:
            reset_count = 0
            error_count = 0

            # Get all active users
            free_users = UserOperations.get_users_by_subscription_type(SubscriptionType.FREE, active_only=True)
            premium_users = UserOperations.get_users_by_subscription_type(SubscriptionType.PREMIUM, active_only=True)
            all_users = free_users + premium_users

            for user in all_users:
                try:
                    # Check if reset is needed
                    reset_needed = UserOperations.check_and_reset_monthly_usage(user.telegram_id)
                    if reset_needed:
                        reset_count += 1
                        # Clear cache for this user
                        usage_limiter._clear_cache(user.telegram_id)
                except Exception as e:
                    logger.error(f"Error resetting usage for user {user.telegram_id}: {e}")
                    error_count += 1

            logger.info(f"Bulk reset completed: {reset_count} users reset, {error_count} errors")

            return {
                "total_users_processed": len(all_users),
                "reset_count": reset_count,
                "error_count": error_count,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in bulk reset monthly usage: {e}")
            return {
                "total_users_processed": 0,
                "reset_count": 0,
                "error_count": 1,
                "error": str(e)
            }

    def _get_current_limits(self) -> Dict[str, int]:
        """Get current limit configuration from database."""
        try:
            cache_key = "current_limits"

            # Check cache
            if cache_key in self._config_cache:
                cached = self._config_cache[cache_key]
                age = (datetime.utcnow() - cached['timestamp']).total_seconds()
                if age < self._config_cache_ttl:
                    return cached['data']

            # Get from database
            with get_db_session() as session:
                configs = session.query(SystemConfig).filter(
                    SystemConfig.config_key.in_([
                        'free_monthly_limit',
                        'premium_monthly_limit',
                        'channel_bonus_requests',
                        'max_bonus_requests'
                    ])
                ).all()

                limits = {}
                for config in configs:
                    limits[config.config_key] = config.get_typed_value()

                # Cache the result
                self._config_cache[cache_key] = {
                    'data': limits,
                    'timestamp': datetime.utcnow()
                }

                return limits

        except Exception as e:
            logger.error(f"Error getting current limits: {e}")
            return {
                'free_monthly_limit': 10,
                'premium_monthly_limit': 100,
                'channel_bonus_requests': 5,
                'max_bonus_requests': 20
            }


# Global limit manager instance
limit_manager = LimitManager()