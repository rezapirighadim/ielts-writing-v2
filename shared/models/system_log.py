"""
System log model for application logging and monitoring.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, Text, DateTime, ForeignKey, String
from ..database import Base
from ..constants import LogLevel


class SystemLog(Base):
    """
    Model for storing system logs and events.
    """

    __tablename__ = 'system_logs'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Log information
    level = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    module = Column(String(100), nullable=True, index=True)

    # User context (optional)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    telegram_id = Column(BigInteger, nullable=True, index=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, level={self.level}, module='{self.module}')>"

    def __str__(self) -> str:
        return f"[{self.level}] {self.module}: {self.message[:50]}..."

    @classmethod
    def create_log(cls, level: str, message: str, module: str = None,
                   user_id: int = None, telegram_id: int = None):
        """
        Create a new log entry.

        Args:
            level: Log level (INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            module: Module name where log originated
            user_id: Associated user ID (optional)
            telegram_id: Associated Telegram user ID (optional)

        Returns:
            SystemLog: New log instance
        """
        return cls(
            level=level.upper(),
            message=message,
            module=module,
            user_id=user_id,
            telegram_id=telegram_id
        )

    def to_dict(self) -> dict:
        """Convert log to dictionary."""
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'module': self.module,
            'user_id': self.user_id,
            'telegram_id': self.telegram_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }