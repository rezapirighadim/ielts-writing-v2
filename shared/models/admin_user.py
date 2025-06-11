"""
Admin user model for Django admin panel authentication.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from ..database import Base
from ..constants import AdminRole


class AdminUser(Base):
    """
    Admin user model for Django admin panel.
    Note: This is a backup model. Django will use its own auth_user table.
    """

    __tablename__ = 'admin_users'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Authentication
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)

    # Status and permissions
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(SQLEnum(AdminRole), default=AdminRole.ADMIN, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<AdminUser(id={self.id}, username='{self.username}', role={self.role.value})>"

    def __str__(self) -> str:
        return f"{self.username} ({self.role.value})"

    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return self.role == AdminRole.SUPER_ADMIN

    def to_dict(self) -> dict:
        """Convert admin user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'role': self.role.value,
            'is_super_admin': self.is_super_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }