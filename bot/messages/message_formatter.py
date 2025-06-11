"""
Message formatting utilities for Persian text and Telegram formatting.
"""

from typing import List, Dict, Any
from datetime import datetime
import re


def format_persian_text(text: str) -> str:
    """
    Format Persian text for better display in Telegram.

    Args:
        text: Persian text to format

    Returns:
        str: Formatted text
    """
    if not text:
        return ""

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())

    # Ensure proper spacing around Persian punctuation
    text = re.sub(r'([،؛؟!])([^\s])', r'\1 \2', text)

    return text


def format_score_list(scores: List[Dict[str, Any]]) -> str:
    """
    Format a list of scores for display.

    Args:
        scores: List of score dictionaries

    Returns:
        str: Formatted scores text
    """
    if not scores:
        return "موردی یافت نشد"

    formatted_scores = []
    for i, score in enumerate(scores[:5], 1):  # Show last 5 scores
        date_str = score.get('submission_date', 'نامشخص')
        if isinstance(date_str, datetime):
            date_str = date_str.strftime('%Y/%m/%d')

        overall = score.get('overall_score', 0)
        task_type = score.get('task_type', 'نامشخص')

        formatted_scores.append(f"{i}. {date_str} - {task_type}: {overall}/9")

    return "\n".join(formatted_scores)


def format_channel_list(channels: List[Dict[str, Any]], bonus_per_channel: int) -> str:
    """
    Format channel list for display.

    Args:
        channels: List of channel dictionaries
        bonus_per_channel: Bonus requests per channel

    Returns:
        str: Formatted channel list
    """
    if not channels:
        return "کانالی موجود نیست"

    formatted_channels = []
    for i, channel in enumerate(channels, 1):
        title = channel.get('channel_title', 'نام نامشخص')
        username = channel.get('channel_username', '')
        url = f"https://t.me/{username}" if username else "#"

        formatted_channels.append(
            f"{i}. [{title}]({url}) - {bonus_per_channel} درخواست رایگان"
        )

    return "\n".join(formatted_channels)


def escape_markdown(text: str) -> str:
    """
    Escape special characters for Telegram Markdown.

    Args:
        text: Text to escape

    Returns:
        str: Escaped text
    """
    if not text:
        return ""

    # Characters that need escaping in Telegram Markdown V2
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    for char in special_chars:
        text = text.replace(char, f'\\{char}')

    return text


def format_datetime_persian(dt: datetime) -> str:
    """
    Format datetime in Persian format.

    Args:
        dt: Datetime object

    Returns:
        str: Persian formatted datetime
    """
    if not dt:
        return "نامشخص"

    # Persian month names
    persian_months = [
        'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
        'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
    ]

    try:
        # For simplicity, use Gregorian calendar with Persian names
        month_name = persian_months[dt.month - 1] if dt.month <= 12 else str(dt.month)
        return f"{dt.day} {month_name} {dt.year}"
    except (IndexError, AttributeError):
        return dt.strftime('%Y/%m/%d') if dt else "نامشخص"


def create_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    """
    Create a simple progress bar using Unicode characters.

    Args:
        current: Current value
        maximum: Maximum value
        length: Length of progress bar

    Returns:
        str: Progress bar string
    """
    if maximum == 0:
        return "█" * length

    filled = int((current / maximum) * length)
    empty = length - filled

    return "█" * filled + "░" * empty


def format_feedback_text(feedback: str, max_length: int = 1000) -> str:
    """
    Format feedback text for Telegram display.

    Args:
        feedback: Feedback text
        max_length: Maximum length for Telegram message

    Returns:
        str: Formatted feedback
    """
    if not feedback:
        return "بازخورد موجود نیست"

    # Format Persian text
    formatted = format_persian_text(feedback)

    # Truncate if too long
    if len(formatted) > max_length:
        formatted = formatted[:max_length - 50] + "\n\n... (متن کامل در ادامه)"

    return formatted