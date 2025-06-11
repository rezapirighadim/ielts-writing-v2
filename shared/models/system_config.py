"""
System configuration model for storing application settings.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from ..database import Base


class ConfigType:
    """Configuration value types."""
    INT = "int"
    STRING = "string"
    BOOLEAN = "boolean"
    JSON = "json"


class SystemConfig(Base):
    """
    Model for storing system configuration key-value pairs.
    """

    __tablename__ = 'system_config'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Configuration data
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    config_type = Column(String(20), default=ConfigType.STRING, nullable=False)

    # Timestamp
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<SystemConfig(key='{self.config_key}', type={self.config_type})>"

    def __str__(self) -> str:
        return f"{self.config_key}: {self.config_value} ({self.config_type})"

    def get_typed_value(self):
        """
        Get the configuration value with proper type conversion.

        Returns:
            The value converted to the appropriate Python type
        """
        if self.config_type == ConfigType.INT:
            try:
                return int(self.config_value)
            except (ValueError, TypeError):
                return 0

        elif self.config_type == ConfigType.BOOLEAN:
            return self.config_value.lower() in ('true', '1', 'yes', 'on')

        elif self.config_type == ConfigType.JSON:
            try:
                import json
                return json.loads(self.config_value)
            except (ValueError, TypeError):
                return {}

        else:  # STRING or default
            return self.config_value

    def set_typed_value(self, value):
        """
        Set the configuration value with automatic type conversion.

        Args:
            value: The value to set (will be converted to string for storage)
        """
        if self.config_type == ConfigType.JSON:
            import json
            self.config_value = json.dumps(value)
        else:
            self.config_value = str(value)

        self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'typed_value': self.get_typed_value(),
            'description': self.description,
            'config_type': self.config_type,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }