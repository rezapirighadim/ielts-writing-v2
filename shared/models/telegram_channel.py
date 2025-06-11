"""
Telegram channel model for managing bonus request channels.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from ..database import Base


class TelegramChannel(Base):
    """
    Model representing Telegram channels that provide bonus requests.
    """

    __tablename__ = 'telegram_channels'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Channel information
    channel_username = Column(String(255), unique=True, nullable=False, index=True)  # Without @
    channel_title = Column(String(255), nullable=False)
    channel_id = Column(BigInteger, unique=True, nullable=False, index=True)

    # Bonus configuration
    bonus_requests = Column(Integer, default=5, nullable=False)

    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    user_memberships = relationship("UserChannelMembership", back_populates="channel", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TelegramChannel(id={self.id}, username=@{self.channel_username}, active={self.is_active})>"

    def __str__(self) -> str:
        return f"@{self.channel_username} ({self.bonus_requests} bonus requests)"

    @property
    def channel_url(self) -> str:
        """Get the Telegram channel URL."""
        return f"https://t.me/{self.channel_username}"

    @property
    def formatted_username(self) -> str:
        """Get username with @ prefix."""
        return f"@{self.channel_username}"

    def to_dict(self) -> dict:
        """Convert channel to dictionary."""
        return {
            'id': self.id,
            'channel_username': self.channel_username,
            'formatted_username': self.formatted_username,
            'channel_title': self.channel_title,
            'channel_id': self.channel_id,
            'channel_url': self.channel_url,
            'bonus_requests': self.bonus_requests,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'description': self.description
        }