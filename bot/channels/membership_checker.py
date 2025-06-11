"""
Telegram channel membership verification system.
"""

import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError
from shared.database import get_db_session
from shared.models.telegram_channel import TelegramChannel
from shared.models.user_channel_membership import UserChannelMembership
from shared.models.system_log import SystemLog
from database.channel_operations import ChannelOperations

logger = logging.getLogger(__name__)

@dataclass
class MembershipResult:
    """
    Result of membership verification.

    Python Concept: Dataclasses provide clean data structures
    with automatic initialization and string representation.
    """
    channel_id: int
    channel_username: str
    channel_title: str
    user_id: int
    telegram_id: int
    is_member: bool
    was_member_before: bool
    bonus_eligible: bool
    bonus_amount: int
    error_message: Optional[str] = None
    check_timestamp: datetime = None

    def __post_init__(self):
        if self.check_timestamp is None:
            self.check_timestamp = datetime.utcnow()

class MembershipChecker:
    """
    Handles Telegram channel membership verification.

    Python Concept: This class encapsulates the complex logic
    of checking membership status via Telegram API.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self._check_timeout = 10  # seconds

    async def check_user_membership(self, telegram_id: int, channel_username: str,
                                  user_id: int = None) -> MembershipResult:
        """
        Check if user is member of specific channel.

        Args:
            telegram_id: Telegram user ID
            channel_username: Channel username (without @)
            user_id: Database user ID (optional)

        Returns:
            MembershipResult: Verification result
        """
        try:
            # Get channel from database
            channel = ChannelOperations.get_channel_by_username(channel_username)
            if not channel:
                return MembershipResult(
                    channel_id=0,
                    channel_username=channel_username,
                    channel_title="Unknown",
                    user_id=user_id or 0,
                    telegram_id=telegram_id,
                    is_member=False,
                    was_member_before=False,
                    bonus_eligible=False,
                    bonus_amount=0,
                    error_message="کانال در سیستم یافت نشد"
                )

            # Get previous membership status
            previous_membership = self._get_previous_membership_status(
                user_id or 0, channel.id
            )
            was_member_before = previous_membership.get('is_member', False) if previous_membership else False
            bonus_already_granted = previous_membership.get('bonus_granted', False) if previous_membership else False

            # Check current membership via Telegram API
            current_is_member = await self._check_telegram_membership(
                telegram_id, channel.channel_id
            )

            # Determine bonus eligibility
            bonus_eligible = (
                current_is_member and  # Currently a member
                not bonus_already_granted and  # Bonus not already granted
                channel.is_active  # Channel is active
            )

            result = MembershipResult(
                channel_id=channel.id,
                channel_username=channel.channel_username,
                channel_title=channel.channel_title,
                user_id=user_id or 0,
                telegram_id=telegram_id,
                is_member=current_is_member,
                was_member_before=was_member_before,
                bonus_eligible=bonus_eligible,
                bonus_amount=channel.bonus_requests if bonus_eligible else 0
            )

            # Update membership status in database
            await self._update_membership_record(result)

            # Log the check
            await self._log_membership_check(result)

            return result

        except Exception as e:
            logger.error(f"Error checking membership for user {telegram_id} in @{channel_username}: {e}")
            return MembershipResult(
                channel_id=0,
                channel_username=channel_username,
                channel_title="Error",
                user_id=user_id or 0,
                telegram_id=telegram_id,
                is_member=False,
                was_member_before=False,
                bonus_eligible=False,
                bonus_amount=0,
                error_message=str(e)
            )

    async def check_multiple_channels(self, telegram_id: int, user_id: int = None) -> List[MembershipResult]:
        """
        Check user membership in all active channels.

        Args:
            telegram_id: Telegram user ID
            user_id: Database user ID (optional)

        Returns:
            List[MembershipResult]: Results for all channels
        """
        try:
            # Get all active channels
            active_channels = ChannelOperations.get_active_channels()
            results = []

            for channel in active_channels:
                result = await self.check_user_membership(
                    telegram_id=telegram_id,
                    channel_username=channel.channel_username,
                    user_id=user_id
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error checking multiple channels for user {telegram_id}: {e}")
            return []

    async def _check_telegram_membership(self, telegram_id: int, channel_id: int) -> bool:
        """
        Check membership via Telegram API.

        Args:
            telegram_id: Telegram user ID
            channel_id: Telegram channel ID

        Returns:
            bool: True if user is member, False otherwise
        """
        try:
            # Get chat member info from Telegram
            chat_member = await self.bot.get_chat_member(
                chat_id=channel_id,
                user_id=telegram_id
            )

            # Check if user is an active member
            # Valid statuses: 'creator', 'administrator', 'member'
            # Invalid statuses: 'left', 'kicked', 'restricted'
            active_statuses = ['creator', 'administrator', 'member']
            is_member = chat_member.status in active_statuses

            logger.debug(f"Telegram API check: User {telegram_id} in channel {channel_id} - Status: {chat_member.status}, Member: {is_member}")

            return is_member

        except TelegramError as e:
            # Handle specific Telegram errors
            if "chat not found" in str(e).lower():
                logger.warning(f"Channel {channel_id} not found or bot not added")
                return False
            elif "user not found" in str(e).lower():
                logger.warning(f"User {telegram_id} not found in channel {channel_id}")
                return False
            elif "forbidden" in str(e).lower():
                logger.warning(f"Bot doesn't have permission to check membership in channel {channel_id}")
                return False
            else:
                logger.error(f"Telegram API error checking membership: {e}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error checking Telegram membership: {e}")
            return False

    def _get_previous_membership_status(self, user_id: int, channel_id: int) -> Optional[Dict[str, Any]]:
        """
        Get previous membership status from database.

        Args:
            user_id: Database user ID
            channel_id: Database channel ID

        Returns:
            dict: Previous membership info or None
        """
        try:
            with get_db_session() as session:
                membership = session.query(UserChannelMembership).filter_by(
                    user_id=user_id,
                    channel_id=channel_id
                ).first()

                if membership:
                    return {
                        'is_member': membership.is_member,
                        'bonus_granted': membership.bonus_granted,
                        'last_check': membership.last_check
                    }
                return None

        except Exception as e:
            logger.error(f"Error getting previous membership status: {e}")
            return None

    async def _update_membership_record(self, result: MembershipResult) -> bool:
        """
        Update membership record in database.

        Args:
            result: Membership verification result

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success, bonus_granted = ChannelOperations.update_user_membership(
                user_id=result.user_id,
                channel_id=result.channel_id,
                is_member=result.is_member
            )

            if success:
                logger.debug(f"Updated membership record for user {result.user_id} in channel {result.channel_id}")
                # Update result with actual bonus status
                if bonus_granted:
                    result.bonus_eligible = True
                    logger.info(f"Bonus granted to user {result.telegram_id} for channel @{result.channel_username}")

            return success

        except Exception as e:
            logger.error(f"Error updating membership record: {e}")
            return False

    async def _log_membership_check(self, result: MembershipResult) -> None:
        """
        Log membership check to system logs.

        Args:
            result: Membership verification result
        """
        try:
            with get_db_session() as session:
                log_message = (
                    f"Membership check: @{result.channel_username}, "
                    f"member={result.is_member}, "
                    f"bonus_eligible={result.bonus_eligible}"
                )

                if result.error_message:
                    log_message += f", error={result.error_message}"

                log_entry = SystemLog.create_log(
                    level="INFO" if not result.error_message else "WARNING",
                    message=log_message,
                    module="membership_checker",
                    user_id=result.user_id if result.user_id > 0 else None,
                    telegram_id=result.telegram_id
                )
                session.add(log_entry)

        except Exception as e:
            logger.error(f"Error logging membership check: {e}")