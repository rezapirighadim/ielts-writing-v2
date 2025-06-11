"""
Session manager for tracking user sessions and conversation states.
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from .conversation_state import ConversationState, ConversationStep

logger = logging.getLogger(__name__)


class UserSession:
    """
    Represents a user's session with conversation state and metadata.

    Python Concept: This class combines user information with their
    current conversation state for easy session management.
    """

    def __init__(self, user_id: int, telegram_id: int, username: str = None):
        self.user_id = user_id
        self.telegram_id = telegram_id
        self.username = username
        self.conversation_state = ConversationState(user_id, telegram_id)
        self.last_message_id: Optional[int] = None
        self.last_command: Optional[str] = None
        self.message_count = 0
        self.session_start = datetime.utcnow()
        self.last_activity = datetime.utcnow()

    def update_activity(self, message_id: int = None, command: str = None) -> None:
        """
        Update session activity.

        Args:
            message_id: Latest message ID (optional)
            command: Latest command used (optional)
        """
        self.last_activity = datetime.utcnow()
        self.message_count += 1

        if message_id:
            self.last_message_id = message_id

        if command:
            self.last_command = command

    def get_session_duration(self) -> timedelta:
        """Get the duration of the current session."""
        return self.last_activity - self.session_start

    def is_conversation_expired(self) -> bool:
        """Check if conversation state has expired."""
        return self.conversation_state.is_expired()

    def reset_conversation(self) -> None:
        """Reset conversation to idle state."""
        self.conversation_state.reset_to_idle()

    def to_dict(self) -> Dict:
        """Convert session to dictionary."""
        return {
            'user_id': self.user_id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'conversation_state': self.conversation_state.to_dict(),
            'last_message_id': self.last_message_id,
            'last_command': self.last_command,
            'message_count': self.message_count,
            'session_start': self.session_start.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'session_duration_seconds': self.get_session_duration().total_seconds()
        }


class SessionManager:
    """
    Manages user sessions and conversation states.

    Python Concept: This is a singleton-like class that manages all
    active user sessions in memory for fast access.
    """

    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}  # telegram_id -> UserSession
        self._cleanup_interval = timedelta(hours=2)
        self._last_cleanup = datetime.utcnow()

    def get_session(self, telegram_id: int, user_id: int = None, username: str = None) -> UserSession:
        """
        Get or create user session.

        Args:
            telegram_id: Telegram user ID
            user_id: Database user ID (optional)
            username: Username (optional)

        Returns:
            UserSession: User's session
        """
        # Check if session exists
        if telegram_id in self._sessions:
            session = self._sessions[telegram_id]

            # Update username if provided
            if username and session.username != username:
                session.username = username
                logger.info(f"Updated username for session {telegram_id}: {username}")

            return session

        # Create new session
        if user_id is None:
            # Try to get user_id from database
            from database.user_operations import UserOperations
            user = UserOperations.get_user_by_telegram_id(telegram_id)
            user_id = user.id if user else telegram_id  # Fallback to telegram_id

        session = UserSession(user_id, telegram_id, username)
        self._sessions[telegram_id] = session

        logger.info(f"Created new session for user {telegram_id} (@{username})")
        return session

    def update_session_activity(self, telegram_id: int, message_id: int = None, command: str = None) -> None:
        """
        Update session activity.

        Args:
            telegram_id: Telegram user ID
            message_id: Message ID (optional)
            command: Command used (optional)
        """
        if telegram_id in self._sessions:
            self._sessions[telegram_id].update_activity(message_id, command)

    def get_conversation_state(self, telegram_id: int) -> Optional[ConversationState]:
        """
        Get user's conversation state.

        Args:
            telegram_id: Telegram user ID

        Returns:
            ConversationState or None if session doesn't exist
        """
        session = self._sessions.get(telegram_id)
        return session.conversation_state if session else None

    def set_conversation_step(self, telegram_id: int, step: ConversationStep, data: Dict = None) -> bool:
        """
        Set conversation step for user.

        Args:
            telegram_id: Telegram user ID
            step: Conversation step
            data: Additional data (optional)

        Returns:
            bool: True if successful, False if session doesn't exist
        """
        session = self._sessions.get(telegram_id)
        if session:
            session.conversation_state.set_step(step, data)
            logger.debug(f"Set conversation step for {telegram_id}: {step.value}")
            return True
        return False

    def reset_conversation(self, telegram_id: int) -> bool:
        """
        Reset user's conversation to idle.

        Args:
            telegram_id: Telegram user ID

        Returns:
            bool: True if successful, False if session doesn't exist
        """
        session = self._sessions.get(telegram_id)
        if session:
            session.reset_conversation()
            logger.info(f"Reset conversation for user {telegram_id}")
            return True
        return False

    def remove_session(self, telegram_id: int) -> bool:
        """
        Remove user session.

        Args:
            telegram_id: Telegram user ID

        Returns:
            bool: True if session was removed, False if it didn't exist
        """
        if telegram_id in self._sessions:
            del self._sessions[telegram_id]
            logger.info(f"Removed session for user {telegram_id}")
            return True
        return False

    def get_active_sessions(self) -> List[UserSession]:
        """
        Get list of all active sessions.

        Returns:
            List of UserSession objects
        """
        return list(self._sessions.values())

    def get_sessions_by_flow(self, flow_type: str) -> List[UserSession]:
        """
        Get sessions currently in specific flow.

        Args:
            flow_type: Flow type (submission, channel, stats, etc.)

        Returns:
            List of UserSession objects
        """
        return [
            session for session in self._sessions.values()
            if session.conversation_state.get_flow_type() == flow_type
        ]

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired conversation states and old sessions.

        Returns:
            int: Number of sessions cleaned up
        """
        current_time = datetime.utcnow()
        expired_sessions = []
        reset_conversations = 0

        for telegram_id, session in self._sessions.items():
            # Reset expired conversations to idle
            if session.is_conversation_expired():
                session.reset_conversation()
                reset_conversations += 1
                logger.debug(f"Reset expired conversation for user {telegram_id}")

            # Remove very old inactive sessions (24+ hours)
            if current_time - session.last_activity > timedelta(hours=24):
                expired_sessions.append(telegram_id)

        # Remove expired sessions
        for telegram_id in expired_sessions:
            del self._sessions[telegram_id]
            logger.info(f"Removed expired session for user {telegram_id}")

        self._last_cleanup = current_time

        total_cleaned = len(expired_sessions) + reset_conversations
        if total_cleaned > 0:
            logger.info(
                f"Session cleanup: {len(expired_sessions)} sessions removed, {reset_conversations} conversations reset")

        return total_cleaned

    def auto_cleanup_if_needed(self) -> None:
        """Automatically cleanup if enough time has passed since last cleanup."""
        if datetime.utcnow() - self._last_cleanup > self._cleanup_interval:
            self.cleanup_expired_sessions()

    def get_session_statistics(self) -> Dict:
        """
        Get session statistics.

        Returns:
            dict: Session statistics
        """
        total_sessions = len(self._sessions)

        # Count by flow type
        flow_counts = {}
        step_counts = {}

        for session in self._sessions.values():
            flow_type = session.conversation_state.get_flow_type()
            step = session.conversation_state.current_step.value

            flow_counts[flow_type] = flow_counts.get(flow_type, 0) + 1
            step_counts[step] = step_counts.get(step, 0) + 1

        # Calculate average session duration
        if self._sessions:
            avg_duration = sum(
                session.get_session_duration().total_seconds()
                for session in self._sessions.values()
            ) / len(self._sessions)
        else:
            avg_duration = 0

        return {
            'total_active_sessions': total_sessions,
            'flow_distribution': flow_counts,
            'step_distribution': step_counts,
            'average_session_duration_seconds': avg_duration,
            'last_cleanup': self._last_cleanup.isoformat()
        }

    def force_reset_all_conversations(self) -> int:
        """
        Force reset all conversations to idle (emergency function).

        Returns:
            int: Number of conversations reset
        """
        reset_count = 0
        for session in self._sessions.values():
            if session.conversation_state.current_step != ConversationStep.IDLE:
                session.reset_conversation()
                reset_count += 1

        logger.warning(f"Force reset {reset_count} conversations to idle")
        return reset_count


# Global session manager instance
session_manager = SessionManager()