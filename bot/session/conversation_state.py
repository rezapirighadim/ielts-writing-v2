"""
Conversation state management for multi-step bot interactions.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class ConversationStep(Enum):
    """
    Enumeration of conversation steps in bot interactions.

    Python Concept: Enums provide type-safe constants that represent
    different states in the conversation flow.
    """
    # Initial states
    IDLE = "idle"

    # Submission flow states
    SUBMIT_TASK_SELECTION = "submit_task_selection"
    SUBMIT_WAITING_TEXT = "submit_waiting_text"
    SUBMIT_PROCESSING = "submit_processing"

    # Channel membership flow states
    CHANNEL_CHECKING = "channel_checking"
    CHANNEL_BONUS_PROCESSING = "channel_bonus_processing"

    # Stats flow states
    STATS_VIEWING = "stats_viewing"

    # Examples flow states
    EXAMPLES_TASK_SELECTION = "examples_task_selection"
    EXAMPLES_VIEWING = "examples_viewing"

    # Upgrade flow states
    UPGRADE_INFO = "upgrade_info"

    # Error states
    ERROR_RECOVERY = "error_recovery"


class ConversationState:
    """
    Manages conversation state for a user session.

    Python Concept: This class encapsulates all the state information
    needed to track where a user is in a multi-step conversation.
    """

    def __init__(self, user_id: int, telegram_id: int):
        self.user_id = user_id
        self.telegram_id = telegram_id
        self.current_step = ConversationStep.IDLE
        self.data: Dict[str, Any] = {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=1)  # 1 hour timeout

    def set_step(self, step: ConversationStep, data: Dict[str, Any] = None) -> None:
        """
        Set the current conversation step and update data.

        Args:
            step: New conversation step
            data: Additional data to store (optional)
        """
        self.current_step = step
        self.updated_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=1)  # Reset timeout

        if data:
            self.data.update(data)

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Get data value by key.

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            Data value or default
        """
        return self.data.get(key, default)

    def set_data(self, key: str, value: Any) -> None:
        """
        Set data value by key.

        Args:
            key: Data key
            value: Data value
        """
        self.data[key] = value
        self.updated_at = datetime.utcnow()

    def clear_data(self) -> None:
        """Clear all stored data."""
        self.data.clear()
        self.updated_at = datetime.utcnow()

    def reset_to_idle(self) -> None:
        """Reset conversation to idle state."""
        self.current_step = ConversationStep.IDLE
        self.data.clear()
        self.updated_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=1)

    def is_expired(self) -> bool:
        """
        Check if the conversation state has expired.

        Returns:
            bool: True if expired, False otherwise
        """
        return datetime.utcnow() > self.expires_at

    def extend_timeout(self, hours: int = 1) -> None:
        """
        Extend the conversation timeout.

        Args:
            hours: Number of hours to extend
        """
        self.expires_at = datetime.utcnow() + timedelta(hours=hours)
        self.updated_at = datetime.utcnow()

    def is_in_submission_flow(self) -> bool:
        """Check if user is in submission flow."""
        submission_steps = {
            ConversationStep.SUBMIT_TASK_SELECTION,
            ConversationStep.SUBMIT_WAITING_TEXT,
            ConversationStep.SUBMIT_PROCESSING
        }
        return self.current_step in submission_steps

    def is_in_channel_flow(self) -> bool:
        """Check if user is in channel membership flow."""
        channel_steps = {
            ConversationStep.CHANNEL_CHECKING,
            ConversationStep.CHANNEL_BONUS_PROCESSING
        }
        return self.current_step in channel_steps

    def get_flow_type(self) -> str:
        """
        Get the current flow type.

        Returns:
            str: Flow type identifier
        """
        if self.is_in_submission_flow():
            return "submission"
        elif self.is_in_channel_flow():
            return "channel"
        elif self.current_step in {ConversationStep.STATS_VIEWING}:
            return "stats"
        elif self.current_step in {ConversationStep.EXAMPLES_TASK_SELECTION, ConversationStep.EXAMPLES_VIEWING}:
            return "examples"
        elif self.current_step in {ConversationStep.UPGRADE_INFO}:
            return "upgrade"
        else:
            return "idle"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert conversation state to dictionary.

        Returns:
            dict: State data as dictionary
        """
        return {
            'user_id': self.user_id,
            'telegram_id': self.telegram_id,
            'current_step': self.current_step.value,
            'data': self.data.copy(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_expired': self.is_expired(),
            'flow_type': self.get_flow_type()
        }

    def __str__(self) -> str:
        """String representation of conversation state."""
        return f"ConversationState(user_id={self.user_id}, step={self.current_step.value}, flow={self.get_flow_type()})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"ConversationState(user_id={self.user_id}, telegram_id={self.telegram_id}, step={self.current_step.value}, data_keys={list(self.data.keys())}, expires_at={self.expires_at})"