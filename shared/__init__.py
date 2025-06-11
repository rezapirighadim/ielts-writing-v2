"""
Shared utilities package for IELTS Telegram Bot.
This package contains common code used by both the bot and admin panel.
"""

from .config import config, validate_environment

__all__ = ['config', 'validate_environment']