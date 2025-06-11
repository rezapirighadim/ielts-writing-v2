"""
Application constants and enums.
This module defines all the constants used throughout the application.
"""

from enum import Enum


class SubscriptionType(Enum):
    """
    User subscription types.

    Python Concept: Enums provide a way to create named constants
    that are more readable and less error-prone than string literals.
    """
    FREE = "free"
    PREMIUM = "premium"


class TaskType(Enum):
    """IELTS task types."""
    TASK1 = "task1"
    TASK2 = "task2"


class SubmissionStatus(Enum):
    """Submission processing status."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class BroadcastStatus(Enum):
    """Broadcast message status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class BroadcastTarget(Enum):
    """Broadcast target audience."""
    ALL = "all"
    FREE = "free"
    PREMIUM = "premium"
    ACTIVE = "active"


class LogLevel(Enum):
    """System log levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AdminRole(Enum):
    """Admin user roles."""
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


# IELTS Scoring Constants
IELTS_MIN_SCORE = 0.0
IELTS_MAX_SCORE = 9.0
IELTS_SCORE_INCREMENT = 0.5

# Word Count Limits
MIN_WORDS_TASK1 = 150
MIN_WORDS_TASK2 = 250
MAX_WORDS_LIMIT = 500  # Reasonable upper limit

# Bot Command Constants
BOT_COMMANDS = [
    ("start", "شروع کار با ربات"),
    ("help", "راهنمای استفاده"),
    ("submit", "ارسال متن برای بررسی"),
    ("stats", "آمار و نمرات من"),
    ("upgrade", "ارتقاء اکانت"),
    ("examples", "نمونه سوالات آیلتس"),
    ("channels", "کانال‌ها برای درخواست رایگان اضافی")
]

# Time Constants (in seconds)
MESSAGE_TIMEOUT = 30
PROCESSING_TIMEOUT = 120
MEMBERSHIP_CHECK_TIMEOUT = 10

# Default Configuration Values
DEFAULT_FREE_LIMIT = 10
DEFAULT_PREMIUM_LIMIT = 100
DEFAULT_CHANNEL_BONUS = 5
DEFAULT_MAX_BONUS = 20