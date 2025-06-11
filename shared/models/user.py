"""
User model for storing Telegram bot users.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Date, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..database import Base
from ..constants import SubscriptionType

class User(Base):
    """
    User model representing bot users.
    """

    __tablename__ = 'users'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Telegram user information
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    # Registration and activity tracking
    registration_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Subscription information
    subscription_type = Column(
        SQLEnum(SubscriptionType),
        default=SubscriptionType.FREE,
        nullable=False
    )

    # Usage tracking
    monthly_submissions = Column(Integer, default=0, nullable=False)
    last_submission_reset = Column(Date, nullable=True)
    total_submissions = Column(Integer, default=0, nullable=False)
    bonus_requests = Column(Integer, default=0, nullable=False)

    # Relationships - use string references to avoid circular imports
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    channel_memberships = relationship("UserChannelMembership", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"

    def __str__(self) -> str:
        display_name = self.username or self.first_name or f"User_{self.telegram_id}"
        return f"{display_name} ({self.subscription_type.value})"

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username or f"User_{self.telegram_id}"

    @property
    def display_name(self) -> str:
        return self.username or self.full_name

    @property
    def is_premium(self) -> bool:
        return self.subscription_type == SubscriptionType.PREMIUM

    @property
    def monthly_limit(self) -> int:
        from ..config import config
        if self.is_premium:
            return config.PREMIUM_MONTHLY_LIMIT
        else:
            return config.FREE_MONTHLY_LIMIT

    @property
    def available_submissions(self) -> int:
        base_limit = self.monthly_limit
        total_available = base_limit + self.bonus_requests
        remaining = max(0, total_available - self.monthly_submissions)
        return remaining

    def can_submit(self) -> bool:
        return self.available_submissions > 0

    def update_activity(self):
        self.last_activity = datetime.utcnow()

    def reset_monthly_usage_if_needed(self):
        from ..utils import should_reset_monthly_usage

        if should_reset_monthly_usage(self.last_submission_reset):
            self.monthly_submissions = 0
            self.last_submission_reset = date.today()
            return True
        return False

    def use_submission(self) -> bool:
        if not self.can_submit():
            return False

        self.monthly_submissions += 1
        self.total_submissions += 1
        self.update_activity()
        return True

    def add_bonus_requests(self, amount: int) -> int:
        from ..config import config
        max_bonus = config.MAX_BONUS_REQUESTS

        new_total = min(self.bonus_requests + amount, max_bonus)
        added = new_total - self.bonus_requests
        self.bonus_requests = new_total

        return added

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'subscription_type': self.subscription_type.value,
            'is_premium': self.is_premium,
            'monthly_submissions': self.monthly_submissions,
            'total_submissions': self.total_submissions,
            'bonus_requests': self.bonus_requests,
            'monthly_limit': self.monthly_limit,
            'available_submissions': self.available_submissions,
            'is_active': self.is_active
        }