"""
High-level channel management for membership verification and bonus handling.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from telegram import Bot
from .membership_checker import MembershipChecker, MembershipResult
from database.channel_operations import ChannelOperations
from database.user_operations import UserOperations
from limits.limit_manager import limit_manager

logger = logging.getLogger(__name__)


class ChannelManager:
    """
    High-level manager for channel operations and membership verification.

    Python Concept: This class provides a facade pattern that simplifies
    complex channel and membership operations for handlers.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self.membership_checker = MembershipChecker(bot)

    async def verify_and_grant_bonuses(self, telegram_id: int, user_id: int = None) -> Dict[str, Any]:
        """
        Verify user membership in all channels and grant applicable bonuses.

        Args:
            telegram_id: Telegram user ID
            user_id: Database user ID (optional)

        Returns:
            dict: Verification results and bonus information
        """
        try:
            # Get user ID if not provided
            if user_id is None:
                user = UserOperations.get_user_by_telegram_id(telegram_id)
                if not user:
                    return {
                        "success": False,
                        "error": "user_not_found",
                        "message": "کاربر در سیستم یافت نشد"
                    }
                user_id = user.id

            # Check membership in all channels
            membership_results = await self.membership_checker.check_multiple_channels(
                telegram_id=telegram_id,
                user_id=user_id
            )

            # Process bonuses
            total_bonuses_granted = 0
            granted_channels = []
            membership_status = []

            for result in membership_results:
                # Add to status list
                membership_status.append({
                    "channel_username": result.channel_username,
                    "channel_title": result.channel_title,
                    "is_member": result.is_member,
                    "bonus_eligible": result.bonus_eligible,
                    "bonus_amount": result.bonus_amount,
                    "error": result.error_message
                })

                # Grant bonus if eligible
                if result.bonus_eligible and result.bonus_amount > 0:
                    success, bonus_info = limit_manager.grant_channel_bonus(
                        telegram_id=telegram_id,
                        channel_title=result.channel_title,
                        bonus_amount=result.bonus_amount
                    )

                    if success:
                        total_bonuses_granted += bonus_info.get('bonus_added', 0)
                        granted_channels.append({
                            "channel_title": result.channel_title,
                            "channel_username": result.channel_username,
                            "bonus_amount": bonus_info.get('bonus_added', 0)
                        })

            # Get updated user status
            user_limit_info = limit_manager.get_user_limit_summary(telegram_id)

            return {
                "success": True,
                "total_bonuses_granted": total_bonuses_granted,
                "granted_channels": granted_channels,
                "membership_status": membership_status,
                "available_submissions": user_limit_info.get('available_submissions', 0),
                "total_bonus_requests": user_limit_info.get('bonus_requests', 0),
                "message": self._generate_verification_message(
                    total_bonuses_granted, granted_channels, membership_status
                )
            }

        except Exception as e:
            logger.error(f"Error in verify_and_grant_bonuses for {telegram_id}: {e}")
            return {
                "success": False,
                "error": "system_error",
                "message": "خطا در بررسی عضویت کانال‌ها"
            }

    async def check_single_channel_membership(self, telegram_id: int, channel_username: str,
                                              user_id: int = None) -> Dict[str, Any]:
        """
        Check membership in a single channel and grant bonus if applicable.

        Args:
            telegram_id: Telegram user ID
            channel_username: Channel username (without @)
            user_id: Database user ID (optional)

        Returns:
            dict: Single channel verification result
        """
        try:
            # Get user ID if not provided
            if user_id is None:
                user = UserOperations.get_user_by_telegram_id(telegram_id)
                if not user:
                    return {
                        "success": False,
                        "error": "user_not_found",
                        "message": "کاربر در سیستم یافت نشد"
                    }
                user_id = user.id

            # Check membership
            result = await self.membership_checker.check_user_membership(
                telegram_id=telegram_id,
                channel_username=channel_username,
                user_id=user_id
            )

            response = {
                "success": True,
                "channel_username": result.channel_username,
                "channel_title": result.channel_title,
                "is_member": result.is_member,
                "bonus_eligible": result.bonus_eligible,
                "bonus_granted": 0
            }

            # Grant bonus if eligible
            if result.bonus_eligible and result.bonus_amount > 0:
                success, bonus_info = limit_manager.grant_channel_bonus(
                    telegram_id=telegram_id,
                    channel_title=result.channel_title,
                    bonus_amount=result.bonus_amount
                )

                if success:
                    response["bonus_granted"] = bonus_info.get('bonus_added', 0)
                    response[
                        "message"] = f"🎉 با عضویت در {result.channel_title}، {response['bonus_granted']} درخواست رایگان دریافت کردید!"
                else:
                    response["message"] = "عضویت تأیید شد اما خطا در اعطای درخواست رایگان"
            elif result.is_member:
                response["message"] = f"✅ عضویت شما در {result.channel_title} تأیید شد"
            else:
                response["message"] = f"❌ شما در {result.channel_title} عضو نیستید"
                response["success"] = False

            if result.error_message:
                response["error"] = result.error_message
                response["success"] = False
                response["message"] = f"خطا در بررسی عضویت: {result.error_message}"

            return response

        except Exception as e:
            logger.error(f"Error checking single channel membership: {e}")
            return {
                "success": False,
                "error": "system_error",
                "message": "خطا در بررسی عضویت کانال"
            }

    def get_available_channels_for_bonus(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get channels where user can potentially earn bonus requests.

        Args:
            user_id: Database user ID

        Returns:
            List of channels with bonus potential
        """
        try:
            return ChannelOperations.get_channels_for_user_bonus_check(user_id)
        except Exception as e:
            logger.error(f"Error getting available channels for user {user_id}: {e}")
            return []

    def get_user_channel_memberships(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user's current channel memberships.

        Args:
            user_id: Database user ID

        Returns:
            List of user's channel memberships
        """
        try:
            return ChannelOperations.get_user_memberships(user_id)
        except Exception as e:
            logger.error(f"Error getting user memberships for {user_id}: {e}")
            return []

    def _generate_verification_message(self, total_bonuses: int, granted_channels: List[Dict],
                                       membership_status: List[Dict]) -> str:
        """
        Generate verification result message in Persian.

        Args:
            total_bonuses: Total bonuses granted
            granted_channels: Channels that granted bonuses
            membership_status: All channel membership status

        Returns:
            str: Formatted Persian message
        """
        try:
            if total_bonuses > 0:
                message = f"🎉 تبریک! {total_bonuses} درخواست رایگان اضافی دریافت کردید!\n\n"

                # List channels that granted bonuses
                message += "📢 کانال‌هایی که درخواست رایگان اعطا کردند:\n"
                for channel in granted_channels:
                    message += f"• {channel['channel_title']}: +{channel['bonus_amount']}\n"

            else:
                # Check if user is member of any channels
                member_channels = [ch for ch in membership_status if ch['is_member']]

                if member_channels:
                    message = "✅ عضویت شما در کانال‌های زیر تأیید شد:\n"
                    for channel in member_channels:
                        message += f"• {channel['channel_title']}\n"
                    message += "\n💡 شما قبلاً درخواست رایگان این کانال‌ها را دریافت کرده‌اید."
                else:
                    message = "❌ شما در هیچ‌کدام از کانال‌ها عضو نیستید.\n\n"
                    message += "📢 برای دریافت درخواست رایگان، در کانال‌های زیر عضو شوید:\n"

                    for channel in membership_status:
                        if not channel.get('error'):
                            message += f"• {channel['channel_title']}\n"

            return message

        except Exception as e:
            logger.error(f"Error generating verification message: {e}")
            return "بررسی عضویت کانال‌ها انجام شد."