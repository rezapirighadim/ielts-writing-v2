"""
Utility functions shared across the application.
This module contains helper functions used by both bot and admin panel.
"""

import re
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

# Set up logging
logger = logging.getLogger(__name__)


def count_words(text: str) -> int:
    """
    Count words in a text string.

    Python Concept: Regular expressions (regex) are powerful for text processing.
    The \b word boundary ensures we count actual words, not partial matches.

    Args:
        text (str): The text to count words in

    Returns:
        int: Number of words in the text
    """
    if not text or not text.strip():
        return 0

    # Remove extra whitespace and split by word boundaries
    # \w+ matches one or more word characters (letters, digits, underscore)
    words = re.findall(r'\w+', text.strip())
    return len(words)


def validate_word_count(text: str, task_type: str) -> Dict[str, Any]:
    """
    Validate if text meets word count requirements for IELTS tasks.

    Args:
        text (str): The text to validate
        task_type (str): Either 'task1' or 'task2'

    Returns:
        Dict containing validation result and message
    """
    from .constants import MIN_WORDS_TASK1, MIN_WORDS_TASK2, MAX_WORDS_LIMIT

    word_count = count_words(text)
    min_words = MIN_WORDS_TASK1 if task_type == 'task1' else MIN_WORDS_TASK2

    if word_count < min_words:
        return {
            'valid': False,
            'word_count': word_count,
            'message': f'متن شما {word_count} کلمه دارد. حداقل {min_words} کلمه مورد نیاز است.',
            'min_required': min_words
        }

    if word_count > MAX_WORDS_LIMIT:
        return {
            'valid': False,
            'word_count': word_count,
            'message': f'متن شما {word_count} کلمه دارد. حداکثر {MAX_WORDS_LIMIT} کلمه مجاز است.',
            'max_allowed': MAX_WORDS_LIMIT
        }

    return {
        'valid': True,
        'word_count': word_count,
        'message': f'تعداد کلمات: {word_count} ✅',
        'min_required': min_words
    }


def format_score(score: float) -> str:
    """
    Format IELTS score for display.

    Args:
        score (float): The score to format

    Returns:
        str: Formatted score string
    """
    if score is None:
        return "نامشخص"

    # IELTS scores are typically shown with one decimal place
    return f"{score:.1f}"


def get_score_band_description(score: float) -> str:
    """
    Get IELTS band score description in Persian.

    Args:
        score (float): IELTS score (0-9)

    Returns:
        str: Persian description of the score band
    """
    if score >= 8.5:
        return "عالی (Expert User)"
    elif score >= 7.5:
        return "خیلی خوب (Very Good User)"
    elif score >= 6.5:
        return "خوب (Competent User)"
    elif score >= 5.5:
        return "متوسط (Modest User)"
    elif score >= 4.5:
        return "محدود (Limited User)"
    elif score >= 3.5:
        return "بسیار محدود (Extremely Limited User)"
    else:
        return "مبتدی (Non User)"


def sanitize_text(text: str) -> str:
    """
    Sanitize text input by removing potentially harmful content.

    Args:
        text (str): Text to sanitize

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())

    # Remove HTML tags (basic protection)
    text = re.sub(r'<[^>]+>', '', text)

    # Limit length to prevent abuse
    max_length = 5000  # Reasonable limit for IELTS writing
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text


def is_valid_telegram_username(username: str) -> bool:
    """
    Validate Telegram username format.

    Args:
        username (str): Username to validate (without @)

    Returns:
        bool: True if valid, False otherwise
    """
    if not username:
        return False

    # Telegram username rules: 5-32 characters, alphanumeric + underscore
    # Must start with letter, end with alphanumeric
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{3,30}[a-zA-Z0-9]$'
    return bool(re.match(pattern, username))


def get_next_month_reset_date() -> datetime:
    """
    Calculate the next month's reset date for usage limits.

    Returns:
        datetime: First day of next month at midnight
    """
    now = datetime.now()
    if now.month == 12:
        # December -> January of next year
        return datetime(now.year + 1, 1, 1)
    else:
        # Any other month -> next month
        return datetime(now.year, now.month + 1, 1)


def should_reset_monthly_usage(last_reset_date: Optional[datetime]) -> bool:
    """
    Check if monthly usage should be reset.

    Args:
        last_reset_date: Date of last reset, or None if never reset

    Returns:
        bool: True if should reset, False otherwise
    """
    if not last_reset_date:
        return True

    now = datetime.now()
    # Reset if we're in a different month
    return (now.year, now.month) != (last_reset_date.year, last_reset_date.month)


async def safe_async_call(coro, timeout: int = 30) -> Optional[Any]:
    """
    Safely execute an async call with timeout.

    Python Concept: This is a utility for handling async operations
    that might hang or take too long.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds

    Returns:
        Result of the coroutine or None if timeout/error
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Async call timed out after {timeout} seconds")
        return None
    except Exception as e:
        logger.error(f"Error in async call: {e}")
        return None