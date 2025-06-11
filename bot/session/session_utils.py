"""
Utility functions for session management.
"""

import logging
from typing import Optional, Dict, Any
from telegram import Update
from .session_manager import session_manager, UserSession
from .conversation_state import ConversationState, ConversationStep

logger = logging.getLogger(__name__)


def get_user_session_from_update(update: Update) -> Optional[UserSession]:
    """
    Get user session from Telegram update.

    Args:
        update: Telegram update object

    Returns:
        UserSession or None if user not found
    """
    try:
        if not update.effective_user:
            return None

        telegram_user = update.effective_user

        # Get user from database to get user_id
        from database.user_operations import UserOperations
        user = UserOperations.get_user_by_telegram_id(telegram_user.id)

        if not user:
            logger.warning(f"User not found in database: {telegram_user.id}")
            return None

        # Get or create session
        session = session_manager.get_session(
            telegram_id=telegram_user.id,
            user_id=user.id,
            username=telegram_user.username
        )

        # Update activity
        message_id = update.message.message_id if update.message else None
        session_manager.update_session_activity(
            telegram_id=telegram_user.id,
            message_id=message_id
        )

        return session

    except Exception as e:
        logger.error(f"Error getting user session from update: {e}")
        return None


def get_conversation_state_from_update(update: Update) -> Optional[ConversationState]:
    """
    Get conversation state from Telegram update.

    Args:
        update: Telegram update object

    Returns:
        ConversationState or None if not found
    """
    session = get_user_session_from_update(update)
    return session.conversation_state if session else None


def set_user_conversation_step(update: Update, step: ConversationStep, data: Dict[str, Any] = None) -> bool:
    """
    Set conversation step for user from update.

    Args:
        update: Telegram update object
        step: Conversation step to set
        data: Additional data to store

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not update.effective_user:
            return False

        telegram_id = update.effective_user.id
        return session_manager.set_conversation_step(telegram_id, step, data)

    except Exception as e:
        logger.error(f"Error setting conversation step: {e}")
        return False


def reset_user_conversation(update: Update) -> bool:
    """
    Reset user conversation to idle from update.

    Args:
        update: Telegram update object

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not update.effective_user:
            return False

        telegram_id = update.effective_user.id
        return session_manager.reset_conversation(telegram_id)

    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        return False


def is_user_in_conversation(update: Update) -> bool:
    """
    Check if user is in active conversation (not idle).

    Args:
        update: Telegram update object

    Returns:
        bool: True if in conversation, False if idle or error
    """
    conversation_state = get_conversation_state_from_update(update)
    if conversation_state:
        return conversation_state.current_step != ConversationStep.IDLE
    return False


def get_user_conversation_data(update: Update, key: str, default: Any = None) -> Any:
    """
    Get conversation data for user.

    Args:
        update: Telegram update object
        key: Data key
        default: Default value if not found

    Returns:
        Data value or default
    """
    conversation_state = get_conversation_state_from_update(update)
    if conversation_state:
        return conversation_state.get_data(key, default)
    return default


def set_user_conversation_data(update: Update, key: str, value: Any) -> bool:
    """
    Set conversation data for user.

    Args:
        update: Telegram update object
        key: Data key
        value: Data value

    Returns:
        bool: True if successful, False otherwise
    """
    conversation_state = get_conversation_state_from_update(update)
    if conversation_state:
        conversation_state.set_data(key, value)
        return True
    return False


def cleanup_sessions() -> int:
    """
    Manually trigger session cleanup.

    Returns:
        int: Number of sessions cleaned up
    """
    return session_manager.cleanup_expired_sessions()


def get_active_session_count() -> int:
    """
    Get count of active sessions.

    Returns:
        int: Number of active sessions
    """
    return len(session_manager.get_active_sessions())


def get_session_statistics() -> Dict[str, Any]:
    """
    Get session manager statistics.

    Returns:
        dict: Session statistics
    """
    return session_manager.get_session_statistics()