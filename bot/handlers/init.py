"""
Bot handlers package for command and message processing.
"""

from .basic_handlers import register_basic_handlers
from .channel_handlers import register_channel_handlers
from .user_handler import (
    ensure_user_exists,
    get_user_from_update,
    get_user_status_summary,
    handle_user_registration_flow,
    check_user_submission_eligibility,
    format_user_statistics,
    log_user_action
)
from .user_utils import (
    get_user_by_telegram_id,
    increment_user_submissions,
    add_bonus_requests_to_user,
    get_user_submission_history,
    check_user_active_status
)
from .bonus_manager import bonus_manager

__all__ = [
    'register_basic_handlers',
    'register_channel_handlers',
    'ensure_user_exists',
    'get_user_from_update',
    'get_user_status_summary',
    'handle_user_registration_flow',
    'check_user_submission_eligibility',
    'format_user_statistics',
    'log_user_action',
    'get_user_by_telegram_id',
    'increment_user_submissions',
    'add_bonus_requests_to_user',
    'get_user_submission_history',
    'check_user_active_status',
    'bonus_manager'
]