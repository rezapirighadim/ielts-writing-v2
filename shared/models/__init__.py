"""
Database models package for IELTS Telegram Bot.
Contains all SQLAlchemy model definitions.
"""

# Import models directly - no circular imports since models don't import each other
from .admin_user import AdminUser
from .system_config import SystemConfig
from .telegram_channel import TelegramChannel
from .user import User
from .submission import Submission
from .user_channel_membership import UserChannelMembership
from .broadcast_message import BroadcastMessage
from .system_log import SystemLog

# Export everything
__all__ = [
    'AdminUser',
    'SystemConfig',
    'TelegramChannel',
    'User',
    'Submission',
    'UserChannelMembership',
    'BroadcastMessage',
    'SystemLog'
]