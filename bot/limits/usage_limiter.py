"""
Usage limiter for managing monthly submission limits.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, date
from dataclasses import dataclass
from shared.constants import SubscriptionType
from database.user_operations import UserOperations
from .limit_exceptions import LimitExceededException

logger = logging.getLogger(__name__)


@dataclass
class LimitCheckResult:
    """
    Result of a limit check operation.

    Python Concept: Dataclasses provide a clean way to structure
    data with automatic __init__, __repr__, and comparison methods.
    """
    can_proceed: bool
    current_usage: int
    limit: int
    bonus_requests: int
    available_submissions: int
    reset_date: Optional[date]
    limit_type: str
    message: str


class UsageLimiter:
    """
    Manages usage limits for bot users.

    Python Concept: This class encapsulates all logic related to
    checking and enforcing usage limits.
    """

    def __init__(self):
        self._cache = {}  # Simple cache for frequent limit checks
        self._cache_ttl = 300  # 5 minutes cache TTL

    def check_submission_limit(self, telegram_id: int) -> LimitCheckResult:
        """
        Check if user can submit based on their limits.

        Args:
            telegram_id: Telegram user ID

        Returns:
            LimitCheckResult: Detailed result of limit check
        """
        try:
            # Get user data
            user_stats = UserOperations.get_user_stats(telegram_id)
            if not user_stats:
                return LimitCheckResult(
                    can_proceed=False,
                    current_usage=0,
                    limit=0,
                    bonus_requests=0,
                    available_submissions=0,
                    reset_date=None,
                    limit_type="unknown",
                    message="کاربر یافت نشد"
                )

            # Check and reset monthly usage if needed
            UserOperations.check_and_reset_monthly_usage(telegram_id)

            # Get fresh user stats after potential reset
            user_stats = UserOperations.get_user_stats(telegram_id)

            # Calculate available submissions
            base_limit = user_stats['monthly_limit']
            bonus_requests = user_stats['bonus_requests']
            current_usage = user_stats['monthly_submissions']
            total_available = base_limit + bonus_requests
            available = max(0, total_available - current_usage)

            # Determine limit type
            limit_type = "premium" if user_stats['is_premium'] else "free"

            # Calculate next reset date
            now = datetime.now()
            if now.month == 12:
                reset_date = date(now.year + 1, 1, 1)
            else:
                reset_date = date(now.year, now.month + 1, 1)

            # Check if user can proceed
            can_proceed = available > 0 and user_stats['is_active']

            # Generate appropriate message
            if not user_stats['is_active']:
                message = "حساب کاربری شما غیرفعال است"
            elif can_proceed:
                message = f"شما {available} درخواست باقی‌مانده دارید"
            else:
                message = f"محدودیت ماهانه شما تمام شده است ({current_usage}/{base_limit})"
                if bonus_requests > 0:
                    message += f" + {bonus_requests} درخواست اضافی"

            result = LimitCheckResult(
                can_proceed=can_proceed,
                current_usage=current_usage,
                limit=base_limit,
                bonus_requests=bonus_requests,
                available_submissions=available,
                reset_date=reset_date,
                limit_type=limit_type,
                message=message
            )

            # Cache the result
            self._cache_result(telegram_id, result)

            return result

        except Exception as e:
            logger.error(f"Error checking submission limit for {telegram_id}: {e}")
            return LimitCheckResult(
                can_proceed=False,
                current_usage=0,
                limit=0,
                bonus_requests=0,
                available_submissions=0,
                reset_date=None,
                limit_type="error",
                message="خطا در بررسی محدودیت"
            )

    def consume_submission(self, telegram_id: int) -> bool:
        """
        Consume one submission from user's limit.

        Args:
            telegram_id: Telegram user ID

        Returns:
            bool: True if submission was consumed, False otherwise
        """
        try:
            # Check if user can submit
            limit_check = self.check_submission_limit(telegram_id)
            if not limit_check.can_proceed:
                raise LimitExceededException(
                    limit_check.message,
                    limit_type=limit_check.limit_type,
                    current_usage=limit_check.current_usage,
                    limit=limit_check.limit
                )

            # Increment user submissions
            success = UserOperations.increment_user_submissions(telegram_id)
            if success:
                # Clear cache for this user
                self._clear_cache(telegram_id)
                logger.info(f"Submission consumed for user {telegram_id}")
                return True
            else:
                logger.error(f"Failed to increment submissions for user {telegram_id}")
                return False

        except LimitExceededException:
            raise  # Re-raise limit exceptions
        except Exception as e:
            logger.error(f"Error consuming submission for {telegram_id}: {e}")
            return False

    def add_bonus_requests(self, telegram_id: int, amount: int, reason: str = "Channel membership") -> int:
        """
        Add bonus requests to user account.

        Args:
            telegram_id: Telegram user ID
            amount: Number of bonus requests to add
            reason: Reason for bonus addition

        Returns:
            int: Number of bonus requests actually added
        """
        try:
            added = UserOperations.add_bonus_requests(telegram_id, amount)

            if added > 0:
                # Clear cache for this user
                self._clear_cache(telegram_id)
                logger.info(f"Added {added} bonus requests to user {telegram_id}: {reason}")

            return added

        except Exception as e:
            logger.error(f"Error adding bonus requests to {telegram_id}: {e}")
            return 0

    def get_limit_status(self, telegram_id: int) -> Dict[str, Any]:
        """
        Get comprehensive limit status for user.

        Args:
            telegram_id: Telegram user ID

        Returns:
            dict: Detailed limit status information
        """
        try:
            limit_check = self.check_submission_limit(telegram_id)
            user_stats = UserOperations.get_user_stats(telegram_id)

            if not user_stats:
                return {"error": "User not found"}

            # Calculate usage percentage
            usage_percentage = 0
            if limit_check.limit > 0:
                usage_percentage = (limit_check.current_usage / limit_check.limit) * 100

            # Calculate days until reset
            days_until_reset = 0
            if limit_check.reset_date:
                days_until_reset = (limit_check.reset_date - date.today()).days

            return {
                "telegram_id": telegram_id,
                "username": user_stats.get('username'),
                "subscription_type": user_stats.get('subscription_type'),
                "is_premium": user_stats.get('is_premium'),
                "current_usage": limit_check.current_usage,
                "monthly_limit": limit_check.limit,
                "bonus_requests": limit_check.bonus_requests,
                "available_submissions": limit_check.available_submissions,
                "total_submissions": user_stats.get('total_submissions'),
                "usage_percentage": round(usage_percentage, 1),
                "can_submit": limit_check.can_proceed,
                "reset_date": limit_check.reset_date.isoformat() if limit_check.reset_date else None,
                "days_until_reset": days_until_reset,
                "limit_type": limit_check.limit_type,
                "is_active": user_stats.get('is_active'),
                "last_activity": user_stats.get('last_activity'),
                "status_message": limit_check.message
            }

        except Exception as e:
            logger.error(f"Error getting limit status for {telegram_id}: {e}")
            return {"error": str(e)}

    def upgrade_user_to_premium(self, telegram_id: int) -> bool:
        """
        Upgrade user to premium subscription.

        Args:
            telegram_id: Telegram user ID

        Returns:
            bool: True if upgrade successful, False otherwise
        """
        try:
            success = UserOperations.upgrade_user_to_premium(telegram_id)
            if success:
                # Clear cache for this user
                self._clear_cache(telegram_id)
                logger.info(f"User {telegram_id} upgraded to premium")
            return success
        except Exception as e:
            logger.error(f"Error upgrading user {telegram_id} to premium: {e}")
            return False

    def get_users_near_limit(self, threshold_percentage: float = 80.0) -> list:
        """
        Get users who are near their monthly limit.

        Args:
            threshold_percentage: Percentage threshold for "near limit"

        Returns:
            list: List of user dictionaries near their limit
        """
        try:
            # Get free users (they have lower limits)
            free_users = UserOperations.get_users_by_subscription_type(SubscriptionType.FREE)
            near_limit_users = []

            for user in free_users:
                limit_status = self.get_limit_status(user.telegram_id)
                if (limit_status.get('usage_percentage', 0) >= threshold_percentage and
                        limit_status.get('available_submissions', 0) > 0):
                    near_limit_users.append(limit_status)

            return near_limit_users

        except Exception as e:
            logger.error(f"Error getting users near limit: {e}")
            return []

    def _cache_result(self, telegram_id: int, result: LimitCheckResult) -> None:
        """Cache limit check result for performance."""
        cache_key = f"limit_{telegram_id}"
        self._cache[cache_key] = {
            'result': result,
            'timestamp': datetime.utcnow()
        }

    def _get_cached_result(self, telegram_id: int) -> Optional[LimitCheckResult]:
        """Get cached limit check result if still valid."""
        cache_key = f"limit_{telegram_id}"
        cached = self._cache.get(cache_key)

        if cached:
            # Check if cache is still valid
            age = (datetime.utcnow() - cached['timestamp']).total_seconds()
            if age < self._cache_ttl:
                return cached['result']
            else:
                # Remove expired cache
                del self._cache[cache_key]

        return None

    def _clear_cache(self, telegram_id: int) -> None:
        """Clear cached result for specific user."""
        cache_key = f"limit_{telegram_id}"
        if cache_key in self._cache:
            del self._cache[cache_key]

    def clear_all_cache(self) -> None:
        """Clear all cached results."""
        self._cache.clear()
        logger.info("Cleared all usage limit cache")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            "cached_entries": len(self._cache),
            "cache_ttl_seconds": self._cache_ttl
        }


# Global usage limiter instance
usage_limiter = UsageLimiter()