"""
Database operations for channel management.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from shared.database import get_db_session
from shared.models.telegram_channel import TelegramChannel
from shared.models.user_channel_membership import UserChannelMembership
from shared.models.user import User
from shared.models.system_log import SystemLog

logger = logging.getLogger(__name__)

class ChannelOperations:
    """
    Database operations class for channel management.
    """

    @staticmethod
    def create_channel(channel_username: str, channel_title: str, channel_id: int,
                      bonus_requests: int = 5, description: str = None) -> Optional[TelegramChannel]:
        """
        Create a new telegram channel.

        Args:
            channel_username: Channel username (without @)
            channel_title: Channel display title
            channel_id: Telegram channel ID
            bonus_requests: Bonus requests for membership
            description: Channel description (optional)

        Returns:
            TelegramChannel object if successful, None otherwise
        """
        try:
            with get_db_session() as session:
                # Check if channel already exists
                existing_channel = session.query(TelegramChannel).filter_by(
                    channel_username=channel_username
                ).first()

                if existing_channel:
                    logger.warning(f"Channel already exists: {channel_username}")
                    return existing_channel

                # Create new channel
                new_channel = TelegramChannel(
                    channel_username=channel_username,
                    channel_title=channel_title,
                    channel_id=channel_id,
                    bonus_requests=bonus_requests,
                    description=description,
                    is_active=True,
                    created_at=datetime.utcnow()
                )

                session.add(new_channel)
                session.flush()  # Get the ID

                # Log channel creation
                log_entry = SystemLog.create_log(
                    level="INFO",
                    message=f"Channel created: @{channel_username} ({channel_title})",
                    module="channel_operations"
                )
                session.add(log_entry)

                logger.info(f"Channel created: @{channel_username}")
                return new_channel

        except Exception as e:
            logger.error(f"Error creating channel {channel_username}: {e}")
            return None

    @staticmethod
    def get_channel_by_username(channel_username: str) -> Optional[TelegramChannel]:
        """
        Get channel by username.

        Args:
            channel_username: Channel username (without @)

        Returns:
            TelegramChannel object if found, None otherwise
        """
        try:
            with get_db_session() as session:
                channel = session.query(TelegramChannel).filter_by(
                    channel_username=channel_username
                ).first()
                if channel:
                    session.expunge(channel)
                return channel
        except Exception as e:
            logger.error(f"Error getting channel by username {channel_username}: {e}")
            return None

    @staticmethod
    def get_active_channels() -> List[TelegramChannel]:
        """
        Get all active channels.

        Returns:
            List of active TelegramChannel objects
        """
        try:
            with get_db_session() as session:
                channels = session.query(TelegramChannel).filter_by(is_active=True).all()

                # Detach from session
                for channel in channels:
                    session.expunge(channel)

                return channels
        except Exception as e:
            logger.error(f"Error getting active channels: {e}")
            return []

    @staticmethod
    def update_user_membership(user_id: int, channel_id: int, is_member: bool) -> tuple[bool, bool]:
        """
        Update user channel membership status.

        Args:
            user_id: User database ID
            channel_id: Channel database ID
            is_member: Current membership status

        Returns:
            tuple: (success: bool, bonus_granted: bool)
        """
        try:
            with get_db_session() as session:
                # Get or create membership record
                membership = session.query(UserChannelMembership).filter_by(
                    user_id=user_id,
                    channel_id=channel_id
                ).first()

                if not membership:
                    membership = UserChannelMembership(
                        user_id=user_id,
                        channel_id=channel_id,
                        is_member=False,
                        last_check=datetime.utcnow(),
                        bonus_granted=False
                    )
                    session.add(membership)

                # Update membership status
                bonus_granted = membership.update_membership_status(is_member)

                # Log membership update
                user = session.query(User).filter_by(id=user_id).first()
                channel = session.query(TelegramChannel).filter_by(id=channel_id).first()

                log_entry = SystemLog.create_log(
                    level="INFO",
                    message=f"Membership updated: @{channel.channel_username if channel else 'unknown'}, member={is_member}, bonus_granted={bonus_granted}",
                    module="channel_operations",
                    user_id=user_id,
                    telegram_id=user.telegram_id if user else None
                )
                session.add(log_entry)

                return True, bonus_granted

        except Exception as e:
            logger.error(f"Error updating membership for user {user_id}, channel {channel_id}: {e}")
            return False, False

    @staticmethod
    def get_user_memberships(user_id: int) -> List[Dict[str, Any]]:
        """
        Get user's channel memberships.

        Args:
            user_id: User database ID

        Returns:
            List of membership dictionaries
        """
        try:
            with get_db_session() as session:
                memberships = (
                    session.query(UserChannelMembership, TelegramChannel)
                    .join(TelegramChannel)
                    .filter(UserChannelMembership.user_id == user_id)
                    .filter(TelegramChannel.is_active == True)
                    .all()
                )

                result = []
                for membership, channel in memberships:
                    result.append({
                        'membership_id': membership.id,
                        'channel_id': channel.id,
                        'channel_username': channel.channel_username,
                        'channel_title': channel.channel_title,
                        'channel_url': channel.channel_url,
                        'bonus_requests': channel.bonus_requests,
                        'is_member': membership.is_member,
                        'bonus_granted': membership.bonus_granted,
                        'last_check': membership.last_check
                    })

                return result
        except Exception as e:
            logger.error(f"Error getting memberships for user {user_id}: {e}")
            return []

    @staticmethod
    def check_user_channel_membership(user_id: int, channel_username: str) -> Optional[bool]:
        """
        Check if user is member of specific channel.

        Args:
            user_id: User database ID
            channel_username: Channel username (without @)

        Returns:
            bool: True if member, False if not member, None if channel not found
        """
        try:
            with get_db_session() as session:
                result = (
                    session.query(UserChannelMembership.is_member)
                    .join(TelegramChannel)
                    .filter(UserChannelMembership.user_id == user_id)
                    .filter(TelegramChannel.channel_username == channel_username)
                    .filter(TelegramChannel.is_active == True)
                    .first()
                )

                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error checking membership for user {user_id}, channel {channel_username}: {e}")
            return None

    @staticmethod
    def get_channel_statistics() -> Dict[str, Any]:
        """
        Get channel statistics.

        Returns:
            dict: Channel statistics
        """
        try:
            with get_db_session() as session:
                total_channels = session.query(TelegramChannel).count()
                active_channels = session.query(TelegramChannel).filter_by(is_active=True).count()

                # Total memberships
                total_memberships = session.query(UserChannelMembership).count()
                active_memberships = session.query(UserChannelMembership).filter_by(is_member=True).count()

                # Bonus grants
                bonus_grants = session.query(UserChannelMembership).filter_by(bonus_granted=True).count()

                # Most popular channels
                from sqlalchemy import func
                popular_channels = (
                    session.query(
                        TelegramChannel.channel_username,
                        TelegramChannel.channel_title,
                        func.count(UserChannelMembership.id).label('member_count')
                    )
                    .join(UserChannelMembership)
                    .filter(UserChannelMembership.is_member == True)
                    .filter(TelegramChannel.is_active == True)
                    .group_by(TelegramChannel.id)
                    .order_by(func.count(UserChannelMembership.id).desc())
                    .limit(5)
                    .all()
                )

                return {
                    'total_channels': total_channels,
                    'active_channels': active_channels,
                    'total_memberships': total_memberships,
                    'active_memberships': active_memberships,
                    'bonus_grants': bonus_grants,
                    'popular_channels': [
                        {
                            'username': channel.channel_username,
                            'title': channel.channel_title,
                            'member_count': channel.member_count
                        }
                        for channel in popular_channels
                    ]
                }
        except Exception as e:
            logger.error(f"Error getting channel statistics: {e}")
            return {
                'total_channels': 0,
                'active_channels': 0,
                'total_memberships': 0,
                'active_memberships': 0,
                'bonus_grants': 0,
                'popular_channels': []
            }

    @staticmethod
    def deactivate_channel(channel_username: str, reason: str = "Manual deactivation") -> bool:
        """
        Deactivate a channel.

        Args:
            channel_username: Channel username (without @)
            reason: Reason for deactivation

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                channel = session.query(TelegramChannel).filter_by(
                    channel_username=channel_username
                ).first()

                if channel:
                    channel.is_active = False

                    # Log deactivation
                    log_entry = SystemLog.create_log(
                        level="WARNING",
                        message=f"Channel deactivated: @{channel_username} - {reason}",
                        module="channel_operations"
                    )
                    session.add(log_entry)

                    logger.warning(f"Channel deactivated: @{channel_username}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deactivating channel {channel_username}: {e}")
            return False

    @staticmethod
    def get_channels_for_user_bonus_check(user_id: int) -> List[Dict[str, Any]]:
        """
        Get channels where user can potentially get bonus requests.

        Args:
            user_id: User database ID

        Returns:
            List of channel dictionaries with bonus potential
        """
        try:
            with get_db_session() as session:
                # Get all active channels and user's membership status
                from sqlalchemy import text

                query = text("""
                    SELECT 
                        c.id,
                        c.channel_username,
                        c.channel_title,
                        c.bonus_requests,
                        COALESCE(m.is_member, 0) as is_member,
                        COALESCE(m.bonus_granted, 0) as bonus_granted
                    FROM telegram_channels c
                    LEFT JOIN user_channel_memberships m ON c.id = m.channel_id AND m.user_id = :user_id
                    WHERE c.is_active = 1
                    ORDER BY c.channel_title
                """)

                result = session.execute(query, {'user_id': user_id}).fetchall()

                channels = []
                for row in result:
                    channels.append({
                        'channel_id': row[0],
                        'channel_username': row[1],
                        'channel_title': row[2],
                        'bonus_requests': row[3],
                        'is_member': bool(row[4]),
                        'bonus_granted': bool(row[5]),
                        'can_get_bonus': bool(row[4]) and not bool(row[5]),  # Member but bonus not granted
                        'channel_url': f"https://t.me/{row[1]}"
                    })

                return channels
        except Exception as e:
            logger.error(f"Error getting channels for user bonus check {user_id}: {e}")
            return []