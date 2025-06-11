"""
Broadcast message model for admin panel messaging system.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..database import Base
from ..constants import BroadcastStatus, BroadcastTarget


class BroadcastMessage(Base):
    """
    Model for storing broadcast messages sent from admin panel.
    """

    __tablename__ = 'broadcast_messages'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Message content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Foreign key to admin user (will be nullable for Django integration)
    created_by = Column(Integer, ForeignKey('admin_users.id'), nullable=True, index=True)

    # Scheduling and status
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(BroadcastStatus), default=BroadcastStatus.DRAFT, nullable=False)

    # Target audience
    target_users = Column(SQLEnum(BroadcastTarget), default=BroadcastTarget.ALL, nullable=False)

    # Statistics
    total_users = Column(Integer, default=0, nullable=False)
    sent_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)

    # Relationships (optional, will work with Django admin users too)
    # admin_user = relationship("AdminUser")

    def __repr__(self) -> str:
        return f"<BroadcastMessage(id={self.id}, title='{self.title}', status={self.status.value})>"

    def __str__(self) -> str:
        return f"{self.title} - {self.status.value}"

    @property
    def success_rate(self) -> float:
        """Calculate message delivery success rate."""
        if self.total_users == 0:
            return 0.0
        return (self.sent_count / self.total_users) * 100

    @property
    def is_scheduled(self) -> bool:
        """Check if message is scheduled for future delivery."""
        return self.status == BroadcastStatus.SCHEDULED and self.scheduled_at is not None

    @property
    def is_completed(self) -> bool:
        """Check if broadcast is completed."""
        return self.status == BroadcastStatus.SENT

    def mark_sent(self):
        """Mark broadcast as sent."""
        self.status = BroadcastStatus.SENT
        self.sent_at = datetime.utcnow()

    def mark_failed(self):
        """Mark broadcast as failed."""
        self.status = BroadcastStatus.FAILED

    def update_statistics(self, sent_count: int, failed_count: int, total_users: int = None):
        """Update broadcast statistics."""
        self.sent_count = sent_count
        self.failed_count = failed_count
        if total_users is not None:
            self.total_users = total_users

    def to_dict(self) -> dict:
        """Convert broadcast message to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'status': self.status.value,
            'target_users': self.target_users.value,
            'total_users': self.total_users,
            'sent_count': self.sent_count,
            'failed_count': self.failed_count,
            'success_rate': self.success_rate,
            'is_scheduled': self.is_scheduled,
            'is_completed': self.is_completed
        }