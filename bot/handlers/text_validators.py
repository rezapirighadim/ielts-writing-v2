"""
Text validation utilities for IELTS submissions.
"""

import re
import logging
from typing import Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class TextValidationError(Exception):
    """Custom exception for text validation errors."""
    pass


@dataclass
class TaskRequirements:
    """
    Data class defining requirements for each IELTS task type.

    Python Concept: Dataclasses provide a clean way to define
    structured data with automatic __init__, __repr__, etc.
    """
    min_words: int
    max_words: int
    task_name: str
    description: str


# Task requirements configuration
TASK_REQUIREMENTS = {
    'task1': TaskRequirements(
        min_words=150,
        max_words=200,
        task_name='Task 1',
        description='گراف، جدول، نمودار یا فرآیند'
    ),
    'task2': TaskRequirements(
        min_words=250,
        max_words=350,
        task_name='Task 2',
        description='مقاله نظری یا بحثی'
    )
}


def count_words(text: str) -> int:
    """
    Count words in text using proper word boundary detection.

    Python Concept: This uses regex to properly count words,
    handling punctuation and multiple spaces correctly.

    Args:
        text: Input text to count words in

    Returns:
        int: Number of words in text
    """
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text.strip())

    # Split by word boundaries and filter empty strings
    words = re.findall(r'\b\w+\b', text)

    return len(words)


def check_text_language(text: str) -> Dict[str, Any]:
    """
    Check if text is primarily in English.

    Python Concept: This function uses character analysis
    to estimate if text is in English or other languages.

    Args:
        text: Text to analyze

    Returns:
        dict: Language analysis result
    """
    try:
        # Remove punctuation and spaces for analysis
        alpha_chars = re.sub(r'[^a-zA-Z\u0600-\u06FF]', '', text)

        if not alpha_chars:
            return {
                'is_english': False,
                'confidence': 0.0,
                'detected_language': 'unknown',
                'reason': 'متن شامل حروف قابل تشخیص نیست'
            }

        # Count English characters
        english_chars = len(re.findall(r'[a-zA-Z]', alpha_chars))

        # Count Persian/Arabic characters
        persian_chars = len(re.findall(r'[\u0600-\u06FF]', alpha_chars))

        total_chars = len(alpha_chars)
        english_ratio = english_chars / total_chars if total_chars > 0 else 0
        persian_ratio = persian_chars / total_chars if total_chars > 0 else 0

        # Determine language
        if english_ratio >= 0.7:
            return {
                'is_english': True,
                'confidence': english_ratio,
                'detected_language': 'english',
                'english_ratio': english_ratio,
                'persian_ratio': persian_ratio
            }
        elif persian_ratio >= 0.7:
            return {
                'is_english': False,
                'confidence': persian_ratio,
                'detected_language': 'persian',
                'reason': 'متن به زبان فارسی نوشته شده است',
                'english_ratio': english_ratio,
                'persian_ratio': persian_ratio
            }
        else:
            return {
                'is_english': False,
                'confidence': max(english_ratio, persian_ratio),
                'detected_language': 'mixed',
                'reason': 'متن ترکیبی از زبان‌های مختلف است',
                'english_ratio': english_ratio,
                'persian_ratio': persian_ratio
            }

    except Exception as e:
        logger.error(f"Error in language detection: {e}")
        return {
            'is_english': False,
            'confidence': 0.0,
            'detected_language': 'error',
            'reason': 'خطا در تشخیص زبان'
        }


def check_text_quality(text: str) -> Dict[str, Any]:
    """
    Check basic text quality indicators.

    Args:
        text: Text to analyze

    Returns:
        dict: Quality analysis result
    """
    try:
        issues = []
        warnings = []

        # Check for minimum sentence structure
        sentences = re.split(r'[.!?]+', text)
        actual_sentences = [s.strip() for s in sentences if s.strip()]

        if len(actual_sentences) < 3:
            issues.append("متن شامل کمتر از 3 جمله است")

        # Check for excessive repetition
        words = text.lower().split()
        word_count = {}
        for word in words:
            if len(word) > 3:  # Only check meaningful words
                word_count[word] = word_count.get(word, 0) + 1

        # Check if any word is repeated too much
        total_words = len(words)
        for word, count in word_count.items():
            if count > max(3, total_words * 0.1):  # More than 10% or 3 times
                warnings.append(f"کلمه '{word}' بیش از حد تکرار شده است")

        # Check for very short sentences
        short_sentences = [s for s in actual_sentences if len(s.split()) < 5]
        if len(short_sentences) > len(actual_sentences) * 0.5:
            warnings.append("بیش از نیمی از جملات بسیار کوتاه هستند")

        # Check for proper capitalization
        if not re.search(r'[A-Z]', text):
            issues.append("متن فاقد حروف بزرگ است")

        return {
            'has_issues': len(issues) > 0,
            'issues': issues,
            'warnings': warnings,
            'sentence_count': len(actual_sentences),
            'average_sentence_length': sum(len(s.split()) for s in actual_sentences) / len(
                actual_sentences) if actual_sentences else 0
        }

    except Exception as e:
        logger.error(f"Error in quality check: {e}")
        return {
            'has_issues': True,
            'issues': ['خطا در بررسی کیفیت متن'],
            'warnings': [],
            'sentence_count': 0,
            'average_sentence_length': 0
        }


def validate_submission_text(text: str, task_type: str) -> Dict[str, Any]:
    """
    Comprehensive validation of submitted text for IELTS evaluation.

    Python Concept: This function orchestrates multiple validation checks
    and provides detailed feedback for improving submissions.

    Args:
        text: Submitted text to validate
        task_type: IELTS task type ('task1' or 'task2')

    Returns:
        dict: Validation result with details

    Raises:
        TextValidationError: If validation fails
    """
    try:
        # Get task requirements
        requirements = TASK_REQUIREMENTS.get(task_type)
        if not requirements:
            raise TextValidationError(f"نوع تسک نامعتبر: {task_type}")

        # Basic text checks
        if not text or not text.strip():
            raise TextValidationError("متن ارسالی خالی است")

        text = text.strip()

        # Check text length
        if len(text) < 50:
            raise TextValidationError("متن بسیار کوتاه است (حداقل 50 کاراکتر)")

        if len(text) > 5000:
            raise TextValidationError("متن بسیار طولانی است (حداکثر 5000 کاراکتر)")

        # Count words
        word_count = count_words(text)

        # Check word count requirements
        if word_count < requirements.min_words:
            raise TextValidationError(
                f"تعداد کلمات کافی نیست. حداقل {requirements.min_words} کلمه مورد نیاز است (شما: {word_count} کلمه)"
            )

        # Warn if significantly over recommended length
        if word_count > requirements.max_words + 50:
            logger.warning(f"Text over recommended length: {word_count} words for {task_type}")

        # Check language
        language_result = check_text_language(text)
        if not language_result['is_english']:
            reason = language_result.get('reason', 'متن به زبان انگلیسی نیست')
            raise TextValidationError(f"لطفاً متن را به زبان انگلیسی بنویسید. {reason}")

        # Check basic quality
        quality_result = check_text_quality(text)
        if quality_result['has_issues']:
            issues = quality_result['issues']
            raise TextValidationError(f"مشکل در متن: {', '.join(issues)}")

        # Check for placeholder text or common test phrases
        placeholder_patterns = [
            r'\b(lorem ipsum|test|testing|sample)\b',
            r'\b(asdf|qwerty|1234)\b',
            r'^[A-Za-z\s]{1,20}$'  # Very simple repetitive text
        ]

        for pattern in placeholder_patterns:
            if re.search(pattern, text.lower()):
                raise TextValidationError("متن ارسالی به نظر تستی یا نمونه است. لطفاً متن واقعی ارسال کنید")

        # Success - return validation result
        return {
            'is_valid': True,
            'word_count': word_count,
            'task_type': task_type,
            'task_name': requirements.task_name,
            'character_count': len(text),
            'language_analysis': language_result,
            'quality_analysis': quality_result,
            'meets_requirements': True,
            'validation_message': f"متن معتبر - {word_count} کلمه برای {requirements.task_name}"
        }

    except TextValidationError:
        # Re-raise validation errors
        raise

    except Exception as e:
        logger.error(f"Unexpected error in text validation: {e}")
        raise TextValidationError("خطای غیرمنتظره در اعتبارسنجی متن")


def get_task_requirements_info(task_type: str) -> Dict[str, Any]:
    """
    Get detailed information about task requirements.

    Args:
        task_type: IELTS task type

    Returns:
        dict: Task requirements information
    """
    requirements = TASK_REQUIREMENTS.get(task_type)
    if not requirements:
        return {}

    return {
        'task_type': task_type,
        'task_name': requirements.task_name,
        'description': requirements.description,
        'min_words': requirements.min_words,
        'max_words': requirements.max_words,
        'recommended_range': f"{requirements.min_words}-{requirements.max_words} کلمه"
    }


def format_validation_summary(validation_result: Dict[str, Any]) -> str:
    """
    Format validation result into a readable Persian summary.

    Args:
        validation_result: Result from validate_submission_text

    Returns:
        str: Formatted summary in Persian
    """
    try:
        if not validation_result.get('is_valid', False):
            return "متن نامعتبر است"

        word_count = validation_result.get('word_count', 0)
        task_name = validation_result.get('task_name', 'نامشخص')
        character_count = validation_result.get('character_count', 0)

        summary = f"""✅ **متن معتبر**

📝 **نوع تسک**: {task_name}
📊 **تعداد کلمات**: {word_count}
📏 **تعداد کاراکتر**: {character_count}

🔍 **وضعیت بررسی**:
• طول متن: مناسب
• زبان نگارش: انگلیسی
• کیفیت کلی: قابل قبول

✅ **آماده برای ارزیابی AI**"""

        # Add warnings if any
        quality_analysis = validation_result.get('quality_analysis', {})
        warnings = quality_analysis.get('warnings', [])

        if warnings:
            summary += f"\n\n⚠️ **نکات بهبود**:\n"
            for warning in warnings[:3]:  # Limit to 3 warnings
                summary += f"• {warning}\n"

        return summary

    except Exception as e:
        logger.error(f"Error formatting validation summary: {e}")
        return "خلاصه اعتبارسنجی در دسترس نیست"


def get_improvement_suggestions(text: str, task_type: str) -> Dict[str, Any]:
    """
    Provide suggestions for improving the submitted text.

    Args:
        text: Original text
        task_type: IELTS task type

    Returns:
        dict: Improvement suggestions
    """
    try:
        suggestions = []
        priorities = []

        requirements = TASK_REQUIREMENTS.get(task_type)
        if not requirements:
            return {'suggestions': [], 'priorities': []}

        word_count = count_words(text)

        # Word count suggestions
        if word_count < requirements.min_words:
            shortfall = requirements.min_words - word_count
            priorities.append(f"افزایش {shortfall} کلمه دیگر")
            suggestions.append("متن را گسترش دهید و جزئیات بیشتری اضافه کنید")

        elif word_count > requirements.max_words + 50:
            excess = word_count - requirements.max_words
            suggestions.append(f"متن {excess} کلمه بیش از حد توصیه شده است - سعی کنید مختصرتر باشید")

        # Check sentence variety
        sentences = re.split(r'[.!?]+', text)
        actual_sentences = [s.strip() for s in sentences if s.strip()]

        if len(actual_sentences) < 5:
            suggestions.append("تعداد جملات را افزایش دهید برای بهتر نشان دادن تنوع گرامری")

        # Check for complex sentences
        complex_sentence_indicators = ['because', 'although', 'however', 'furthermore', 'moreover']
        has_complex = any(indicator in text.lower() for indicator in complex_sentence_indicators)

        if not has_complex:
            suggestions.append("از کلمات ربط پیچیده‌تری استفاده کنید (however, furthermore, nevertheless)")

        # Task-specific suggestions
        if task_type == 'task1':
            data_words = ['increase', 'decrease', 'rose', 'fell', 'peak', 'trough', 'trend']
            has_data_language = any(word in text.lower() for word in data_words)

            if not has_data_language:
                suggestions.append("از واژگان تخصصی توصیف داده استفاده کنید (increase, decrease, peak, etc.)")

        elif task_type == 'task2':
            opinion_words = ['believe', 'think', 'opinion', 'argue', 'suggest', 'conclude']
            has_opinion_language = any(word in text.lower() for word in opinion_words)

            if not has_opinion_language:
                suggestions.append("نظرات شخصی خود را با کلمات مناسب بیان کنید (I believe, In my opinion, etc.)")

        return {
            'suggestions': suggestions,
            'priorities': priorities,
            'total_suggestions': len(suggestions),
            'has_priorities': len(priorities) > 0
        }

    except Exception as e:
        logger.error(f"Error generating improvement suggestions: {e}")
        return {
            'suggestions': [],
            'priorities': [],
            'total_suggestions': 0,
            'has_priorities': False
        }