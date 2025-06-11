"""
User channel membership model for tracking Telegram channel memberships.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base


class UserChannelMembership(Base):
    """
    Model representing user memberships in Telegram channels.
    """

    __tablename__ = 'user_channel_memberships'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey('telegram_channels.id', ondelete='CASCADE'), nullable=False, index=True)

    # Membership status
    is_member = Column(Boolean, default=False, nullable=False)
    last_check = Column(DateTime, default=datetime.utcnow, nullable=False)
    bonus_granted = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="channel_memberships")
    channel = relationship("TelegramChannel", back_populates="user_memberships")

    # Unique constraint to prevent duplicate memberships
    __table_args__ = (
        UniqueConstraint('user_id', 'channel_id', name='unique_user_channel'),
    )

    def __repr__(self) -> str:
        return f"<UserChannelMembership(user_id={self.user_id}, channel_id={self.channel_id}, is_member={self.is_member})>"

    def __str__(self) -> str:
        status = "Member" if self.is_member else "Not Member"
        bonus_status = "Bonus Granted" if self.bonus_granted else "No Bonus"
        return f"User {self.user_id} - Channel {self.channel_id}: {status}, {bonus_status}"

    def update_membership_status(self, is_member: bool) -> bool:
        """
        Update membership status and return if bonus should be granted.

        Args:
            is_member: Current membership status

        Returns:
            bool: True if bonus should be granted (newly joined member)
        """
        was_member = self.is_member
        self.is_member = is_member
        self.last_check = datetime.utcnow()

        # Grant bonus if user just became a member and hasn't received bonus yet
        should_grant_bonus = (not was_member and is_member and not self.bonus_granted)

        if should_grant_bonus:
            self.bonus_granted = True

        return should_grant_bonus

    def to_dict(self) -> dict:
        """Convert membership to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'channel_id': self.channel_id,
            'is_member': self.is_member,
            'bonus_granted': self.bonus_granted,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }