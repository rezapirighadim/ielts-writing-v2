"""
Bonus request management for channel memberships.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from database.user_operations import UserOperations
from database.channel_operations import ChannelOperations
from limits.limit_manager import limit_manager
from shared.models.system_log import SystemLog
from shared.database import get_db_session

logger = logging.getLogger(__name__)


class BonusManager:
    """
    Manages bonus request allocation and tracking for channel memberships.

    Python Concept: This class centralizes all bonus-related logic
    and provides a clean interface for bonus operations.
    """

    def __init__(self):
        self._bonus_cache = {}  # Cache for recent bonus operations
        self._cache_ttl = 300  # 5 minutes cache

    def calculate_available_bonuses(self, user_id: int) -> Dict[str, Any]:
        """
        Calculate total available bonus requests for a user.

        Args:
            user_id: Database user ID

        Returns:
            dict: Bonus calculation details
        """
        try:
            # Get user's channel memberships
            memberships = ChannelOperations.get_user_memberships(user_id)

            # Get channels where user can still get bonuses
            available_channels = ChannelOperations.get_channels_for_user_bonus_check(user_id)

            # Calculate statistics
            total_channels = len(available_channels)
            current_memberships = len([m for m in memberships if m.get('is_member', False)])
            eligible_bonuses = len([ch for ch in available_channels if ch.get('can_get_bonus', False)])
            potential_bonus = sum(
                ch.get('bonus_requests', 0) for ch in available_channels if ch.get('can_get_bonus', False))

            # Get user's current bonus requests
            user_stats = UserOperations.get_user_stats(user_id)
            current_bonus = user_stats.get('bonus_requests', 0) if user_stats else 0

            return {
                "success": True,
                "user_id": user_id,
                "total_channels": total_channels,
                "current_memberships": current_memberships,
                "eligible_for_bonus": eligible_bonuses,
                "potential_bonus_requests": potential_bonus,
                "current_bonus_requests": current_bonus,
                "membership_rate": (current_memberships / total_channels * 100) if total_channels > 0 else 0,
                "available_channels": available_channels,
                "current_memberships_detail": memberships
            }

        except Exception as e:
            logger.error(f"Error calculating available bonuses for user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "user_id": user_id
            }

    async def process_membership_bonus(self, user_id: int, channel_id: int,
                                       is_member: bool) -> Tuple[bool, Dict[str, Any]]:
        """
        Process bonus request for channel membership.

        Args:
            user_id: Database user ID
            channel_id: Database channel ID
            is_member: Current membership status

        Returns:
            tuple: (success: bool, details: dict)
        """
        try:
            # Update membership status and check if bonus should be granted
            success, bonus_granted = ChannelOperations.update_user_membership(
                user_id=user_id,
                channel_id=channel_id,
                is_member=is_member
            )

            if not success:
                return False, {
                    "error": "membership_update_failed",
                    "message": "خطا در به‌روزرسانی وضعیت عضویت"
                }

            result = {
                "membership_updated": True,
                "is_member": is_member,
                "bonus_granted": bonus_granted,
                "bonus_amount": 0
            }

            # If bonus was granted, add it to user account
            if bonus_granted:
                # Get channel info to determine bonus amount
                with get_db_session() as session:
                    from shared.models.telegram_channel import TelegramChannel
                    channel = session.query(TelegramChannel).filter_by(id=channel_id).first()

                    if channel:
                        bonus_amount = channel.bonus_requests

                        # Add bonus requests to user account
                        added_bonus = limit_manager.add_bonus_requests(
                            telegram_id=user_id,  # This should be telegram_id, will fix
                            amount=bonus_amount,
                            reason=f"Channel membership: {channel.channel_title}"
                        )

                        result.update({
                            "bonus_amount": added_bonus,
                            "channel_title": channel.channel_title,
                            "channel_username": channel.channel_username
                        })

                        # Log the bonus grant
                        log_entry = SystemLog.create_log(
                            level="INFO",
                            message=f"Bonus granted: {added_bonus} requests for channel @{channel.channel_username}",
                            module="bonus_manager",
                            user_id=user_id
                        )
                        session.add(log_entry)

                        logger.info(
                            f"Bonus granted to user {user_id}: {added_bonus} requests for @{channel.channel_username}")

            return True, result

        except Exception as e:
            logger.error(f"Error processing membership bonus for user {user_id}, channel {channel_id}: {e}")
            return False, {
                "error": "processing_failed",
                "message": f"خطا در پردازش درخواست رایگان: {str(e)}"
            }

    def get_bonus_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get user's bonus request history.

        Args:
            user_id: Database user ID
            limit: Maximum number of records to return

        Returns:
            List of bonus history records
        """
        try:
            with get_db_session() as session:
                # Get bonus-related logs
                bonus_logs = (
                    session.query(SystemLog)
                    .filter(SystemLog.user_id == user_id)
                    .filter(SystemLog.message.like('%bonus%'))
                    .order_by(SystemLog.created_at.desc())
                    .limit(limit)
                    .all()
                )

                history = []
                for log in bonus_logs:
                    history.append({
                        "id": log.id,
                        "message": log.message,
                        "level": log.level,
                        "created_at": log.created_at,
                        "module": log.module
                    })

                return history

        except Exception as e:
            logger.error(f"Error getting bonus history for user {user_id}: {e}")
            return []

    def get_channel_bonus_statistics(self) -> Dict[str, Any]:
        """
        Get system-wide channel bonus statistics.

        Returns:
            dict: Bonus statistics
        """
        try:
            # Get channel statistics
            channel_stats = ChannelOperations.get_channel_statistics()

            # Get user statistics
            user_stats = UserOperations.get_user_count_statistics()

            # Calculate bonus-related metrics
            with get_db_session() as session:
                # Total bonus requests granted
                bonus_logs = session.query(SystemLog).filter(
                    SystemLog.message.like('%bonus granted%')
                ).count()

                # Users with bonus requests
                from shared.models.user import User
                users_with_bonus = session.query(User).filter(
                    User.bonus_requests > 0
                ).count()

            return {
                "channel_statistics": channel_stats,
                "user_statistics": user_stats,
                "total_bonus_grants": bonus_logs,
                "users_with_bonus_requests": users_with_bonus,
                "bonus_utilization_rate": (users_with_bonus / user_stats.get('active_users', 1)) * 100
            }

        except Exception as e:
            logger.error(f"Error getting channel bonus statistics: {e}")
            return {
                "error": str(e),
                "channel_statistics": {},
                "user_statistics": {},
                "total_bonus_grants": 0,
                "users_with_bonus_requests": 0,
                "bonus_utilization_rate": 0
            }

    def validate_bonus_eligibility(self, user_id: int, channel_id: int) -> Tuple[bool, str]:
        """
        Validate if user is eligible for bonus from specific channel.

        Args:
            user_id: Database user ID
            channel_id: Database channel ID

        Returns:
            tuple: (is_eligible: bool, reason: str)
        """
        try:
            # Check if channel exists and is active
            with get_db_session() as session:
                from shared.models.telegram_channel import TelegramChannel
                from shared.models.user_channel_membership import UserChannelMembership

                channel = session.query(TelegramChannel).filter_by(id=channel_id).first()
                if not channel:
                    return False, "کانال یافت نشد"

                if not channel.is_active:
                    return False, "کانال غیرفعال است"

                # Check membership record
                membership = session.query(UserChannelMembership).filter_by(
                    user_id=user_id,
                    channel_id=channel_id
                ).first()

                if not membership:
                    return True, "کاربر هنوز عضو نشده"

                if membership.bonus_granted:
                    return False, "درخواست رایگان قبلاً دریافت شده"

                if not membership.is_member:
                    return True, "کاربر عضو نیست"

                return True, "واجد شرایط دریافت درخواست رایگان"

        except Exception as e:
            logger.error(f"Error validating bonus eligibility: {e}")
            return False, f"خطا در بررسی واجد شرایط بودن: {str(e)}"

    def format_bonus_summary(self, bonus_data: Dict[str, Any]) -> str:
        """
        Format bonus information for display.

        Args:
            bonus_data: Bonus calculation data

        Returns:
            str: Formatted Persian text
        """
        try:
            if not bonus_data.get("success", False):
                return "خطا در دریافت اطلاعات درخواست رایگان"

            total_channels = bonus_data.get("total_channels", 0)
            current_memberships = bonus_data.get("current_memberships", 0)
            eligible_bonuses = bonus_data.get("eligible_for_bonus", 0)
            potential_bonus = bonus_data.get("potential_bonus_requests", 0)
            current_bonus = bonus_data.get("current_bonus_requests", 0)
            membership_rate = bonus_data.get("membership_rate", 0)

            summary = f"""📊 خلاصه درخواست‌های رایگان

🔢 کل کانال‌ها: {total_channels}
✅ عضویت‌های فعلی: {current_memberships}
🎁 قابل دریافت: {eligible_bonuses} کانال
💰 مجموع درخواست رایگان قابل دریافت: {potential_bonus}
💎 درخواست‌های رایگان فعلی: {current_bonus}
📈 درصد عضویت: {membership_rate:.1f}%

💡 با عضویت در کانال‌های باقی‌مانده، {potential_bonus} درخواست رایگان اضافی دریافت کنید!"""

            return summary

        except Exception as e:
            logger.error(f"Error formatting bonus summary: {e}")
            return "خطا در نمایش خلاصه درخواست‌های رایگان"


# Global bonus manager instance
bonus_manager = BonusManager()