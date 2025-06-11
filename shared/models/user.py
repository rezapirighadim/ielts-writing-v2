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

    Python Concept: This class inherits from Base (declarative_base)
    which makes it a SQLAlchemy ORM model. Each attribute becomes a database column.
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

    # Relationships
    # Python Concept: relationships define how models are connected
    # back_populates creates a two-way relationship
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    channel_memberships = relationship("UserChannelMembership", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """
        String representation of the User object.

        Python Concept: __repr__ should provide a clear, unambiguous
        representation of the object, useful for debugging.
        """
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"

    def __str__(self) -> str:
        """
        Human-readable string representation.

        Python Concept: __str__ should provide a nice, human-readable
        representation of the object.
        """
        display_name = self.username or self.first_name or f"User_{self.telegram_id}"
        return f"{display_name} ({self.subscription_type.value})"

    @property
    def full_name(self) -> str:
        """
        Get user's full name.

        Python Concept: @property decorator makes this method accessible
        like an attribute (user.full_name instead of user.full_name())
        """
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
        """Get the best available display name for the user."""
        return self.username or self.full_name

    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription."""
        return self.subscription_type == SubscriptionType.PREMIUM

    @property
    def monthly_limit(self) -> int:
        """Get the monthly submission limit for this user."""
        from ..config import config
        if self.is_premium:
            return config.PREMIUM_MONTHLY_LIMIT
        else:
            return config.FREE_MONTHLY_LIMIT

    @property
    def available_submissions(self) -> int:
        """Calculate available submissions this month including bonuses."""
        base_limit = self.monthly_limit
        total_available = base_limit + self.bonus_requests
        remaining = max(0, total_available - self.monthly_submissions)
        return remaining

    def can_submit(self) -> bool:
        """Check if user can submit a new writing sample."""
        return self.available_submissions > 0

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def reset_monthly_usage_if_needed(self):
        """Reset monthly usage if we're in a new month."""
        from ..utils import should_reset_monthly_usage

        if should_reset_monthly_usage(self.last_submission_reset):
            self.monthly_submissions = 0
            self.last_submission_reset = date.today()
            return True
        return False

    def use_submission(self) -> bool:
        """
        Use one submission from available count.

        Returns:
            bool: True if submission was used, False if no submissions available
        """
        if not self.can_submit():
            return False

        self.monthly_submissions += 1
        self.total_submissions += 1
        self.update_activity()
        return True

    def add_bonus_requests(self, amount: int) -> int:
        """
        Add bonus requests to user account.

        Args:
            amount: Number of bonus requests to add

        Returns:
            int: New total bonus requests
        """
        from ..config import config
        max_bonus = config.MAX_BONUS_REQUESTS

        new_total = min(self.bonus_requests + amount, max_bonus)
        added = new_total - self.bonus_requests
        self.bonus_requests = new_total

        return added

    def to_dict(self) -> dict:
        """
        Convert user object to dictionary.

        Python Concept: Converting ORM objects to dictionaries is useful
        for JSON serialization and API responses.
        """
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