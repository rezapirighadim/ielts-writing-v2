"""
Enhanced word count validation for IELTS submissions.
"""

import re
import logging
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class WordCountMethod(Enum):
    """Different methods for counting words."""
    SIMPLE_SPLIT = "simple_split"
    REGEX_BOUNDARIES = "regex_boundaries"
    ADVANCED_PARSING = "advanced_parsing"


@dataclass
class WordCountResult:
    """
    Data class for word count results.

    Python Concept: Dataclasses provide a clean way to structure
    data with automatic methods and type hints.
    """
    total_words: int
    method_used: WordCountMethod
    breakdown: Dict[str, int]
    warnings: List[str]
    suggestions: List[str]
    is_acceptable: bool
    confidence_score: float


class EnhancedWordCounter:
    """
    Enhanced word counter with multiple counting methods and validation.

    Python Concept: This class provides sophisticated word counting
    that handles edge cases and provides detailed analysis.
    """

    def __init__(self):
        # Common contractions mapping
        self.contractions = {
            "don't": ["do", "not"],
            "won't": ["will", "not"],
            "can't": ["can", "not"],
            "shouldn't": ["should", "not"],
            "wouldn't": ["would", "not"],
            "couldn't": ["could", "not"],
            "isn't": ["is", "not"],
            "aren't": ["are", "not"],
            "wasn't": ["was", "not"],
            "weren't": ["were", "not"],
            "haven't": ["have", "not"],
            "hasn't": ["has", "not"],
            "hadn't": ["had", "not"],
            "I'm": ["I", "am"],
            "you're": ["you", "are"],
            "we're": ["we", "are"],
            "they're": ["they", "are"],
            "it's": ["it", "is"],
            "that's": ["that", "is"],
            "there's": ["there", "is"],
            "here's": ["here", "is"],
            "what's": ["what", "is"],
            "who's": ["who", "is"],
            "I've": ["I", "have"],
            "you've": ["you", "have"],
            "we've": ["we", "have"],
            "they've": ["they", "have"],
            "I'll": ["I", "will"],
            "you'll": ["you", "will"],
            "we'll": ["we", "will"],
            "they'll": ["they", "will"],
            "I'd": ["I", "would"],
            "you'd": ["you", "would"],
            "we'd": ["we", "would"],
            "they'd": ["they", "would"]
        }

    def count_words_simple(self, text: str) -> Tuple[int, Dict[str, int]]:
        """
        Simple word counting by splitting on whitespace.

        Args:
            text: Input text

        Returns:
            tuple: (word_count, breakdown_dict)
        """
        words = text.split()
        non_empty_words = [w for w in words if w.strip()]

        return len(non_empty_words), {
            "total_tokens": len(words),
            "non_empty_tokens": len(non_empty_words),
            "empty_tokens": len(words) - len(non_empty_words)
        }

    def count_words_regex(self, text: str) -> Tuple[int, Dict[str, int]]:
        """
        Word counting using regex word boundaries.

        Args:
            text: Input text

        Returns:
            tuple: (word_count, breakdown_dict)
        """
        # Find all word sequences (letters, numbers, apostrophes)
        words = re.findall(r"\b[\w']+\b", text)

        # Separate different types
        alpha_words = [w for w in words if re.match(r"^[a-zA-Z']+$", w)]
        numeric_words = [w for w in words if re.match(r"^[0-9]+$", w)]
        mixed_words = [w for w in words if
                       re.match(r"^[a-zA-Z0-9']+$", w) and w not in alpha_words and w not in numeric_words]

        return len(words), {
            "total_words": len(words),
            "alphabetic_words": len(alpha_words),
            "numeric_words": len(numeric_words),
            "mixed_words": len(mixed_words)
        }

    def count_words_advanced(self, text: str) -> Tuple[int, Dict[str, int]]:
        """
        Advanced word counting with contraction expansion and smart parsing.

        Args:
            text: Input text

        Returns:
            tuple: (word_count, breakdown_dict)
        """
        # Normalize text
        normalized_text = re.sub(r'\s+', ' ', text.strip())

        # Find potential words
        potential_words = re.findall(r"\b[\w']+\b", normalized_text)

        total_count = 0
        contractions_expanded = 0
        hyphenated_words = 0
        abbreviations = 0
        numbers = 0
        regular_words = 0

        for word in potential_words:
            word_lower = word.lower()

            # Handle contractions
            if word_lower in self.contractions:
                total_count += len(self.contractions[word_lower])
                contractions_expanded += 1

            # Handle hyphenated words (count as separate words)
            elif '-' in word and len(word) > 3:
                parts = [p for p in word.split('-') if p and len(p) > 1]
                total_count += len(parts)
                hyphenated_words += 1

            # Handle abbreviations (count as one word)
            elif re.match(r'^[A-Z]{2,}\.?$', word):
                total_count += 1
                abbreviations += 1

            # Handle numbers
            elif re.match(r'^\d+$', word):
                total_count += 1
                numbers += 1

            # Regular words
            elif len(word) >= 1:
                total_count += 1
                regular_words += 1

        breakdown = {
            "total_words": total_count,
            "regular_words": regular_words,
            "contractions_expanded": contractions_expanded,
            "hyphenated_words": hyphenated_words,
            "abbreviations": abbreviations,
            "numbers": numbers,
            "original_tokens": len(potential_words)
        }

        return total_count, breakdown

    def validate_word_count(self, text: str, task_type: str,
                            min_words: int = None, max_words: int = None) -> WordCountResult:
        """
        Comprehensive word count validation with multiple methods.

        Args:
            text: Text to validate
            task_type: IELTS task type ('task1' or 'task2')
            min_words: Minimum word requirement (optional)
            max_words: Maximum word recommendation (optional)

        Returns:
            WordCountResult: Detailed validation result
        """
        try:
            # Set default requirements based on task type
            if min_words is None:
                min_words = 150 if task_type == 'task1' else 250
            if max_words is None:
                max_words = 200 if task_type == 'task1' else 350

            # Count words using different methods
            simple_count, simple_breakdown = self.count_words_simple(text)
            regex_count, regex_breakdown = self.count_words_regex(text)
            advanced_count, advanced_breakdown = self.count_words_advanced(text)

            # Determine best method and count
            counts = [simple_count, regex_count, advanced_count]
            methods = [WordCountMethod.SIMPLE_SPLIT, WordCountMethod.REGEX_BOUNDARIES, WordCountMethod.ADVANCED_PARSING]

            # Use advanced method as primary, but validate against others
            primary_count = advanced_count
            primary_method = WordCountMethod.ADVANCED_PARSING
            primary_breakdown = advanced_breakdown

            # Calculate confidence based on method agreement
            count_variance = max(counts) - min(counts)
            confidence_score = max(0.5, 1.0 - (count_variance / max(counts)))

            # Generate warnings and suggestions
            warnings = []
            suggestions = []

            # Check count discrepancies
            if count_variance > 5:
                warnings.append(f"تعداد کلمات در روش‌های مختلف متفاوت است ({min(counts)}-{max(counts)})")

            # Check against requirements
            is_acceptable = min_words <= primary_count <= max_words + 50

            if primary_count < min_words:
                shortfall = min_words - primary_count
                suggestions.append(f"نیاز به {shortfall} کلمه بیشتر برای رسیدن به حداقل مورد نیاز")

            elif primary_count > max_words + 50:
                excess = primary_count - max_words
                suggestions.append(f"متن {excess} کلمه بیش از حد توصیه شده است")

            # Task-specific suggestions
            if task_type == 'task1' and primary_count > 200:
                suggestions.append("برای Task 1، بهتر است متن را خلاصه‌تر نگه دارید")
            elif task_type == 'task2' and primary_count < 280:
                suggestions.append("برای Task 2، می‌توانید ایده‌های بیشتری اضافه کنید")

            # Check for potential issues
            if advanced_breakdown.get('numbers', 0) > primary_count * 0.1:
                warnings.append("تعداد زیادی عدد در متن وجود دارد")

            if advanced_breakdown.get('contractions_expanded', 0) > primary_count * 0.2:
                warnings.append("استفاده زیاد از مخففات - در آیلتس بهتر است شکل کامل بنویسید")

            return WordCountResult(
                total_words=primary_count,
                method_used=primary_method,
                breakdown=primary_breakdown,
                warnings=warnings,
                suggestions=suggestions,
                is_acceptable=is_acceptable,
                confidence_score=confidence_score
            )

        except Exception as e:
            logger.error(f"Error in word count validation: {e}")
            return WordCountResult(
                total_words=0,
                method_used=WordCountMethod.SIMPLE_SPLIT,
                breakdown={},
                warnings=["خطا در شمارش کلمات"],
                suggestions=["لطفاً متن را دوباره بررسی کنید"],
                is_acceptable=False,
                confidence_score=0.0
            )

    def compare_counting_methods(self, text: str) -> Dict[str, Any]:
        """
        Compare different word counting methods for analysis.

        Args:
            text: Text to analyze

        Returns:
            dict: Comparison results
        """
        try:
            simple_count, simple_breakdown = self.count_words_simple(text)
            regex_count, regex_breakdown = self.count_words_regex(text)
            advanced_count, advanced_breakdown = self.count_words_advanced(text)

            return {
                "methods": {
                    "simple_split": {
                        "count": simple_count,
                        "breakdown": simple_breakdown
                    },
                    "regex_boundaries": {
                        "count": regex_count,
                        "breakdown": regex_breakdown
                    },
                    "advanced_parsing": {
                        "count": advanced_count,
                        "breakdown": advanced_breakdown
                    }
                },
                "variance": max(simple_count, regex_count, advanced_count) - min(simple_count, regex_count,
                                                                                 advanced_count),
                "recommended_count": advanced_count,
                "agreement_level": "high" if abs(advanced_count - regex_count) <= 2 else "medium" if abs(
                    advanced_count - regex_count) <= 5 else "low"
            }

        except Exception as e:
            logger.error(f"Error comparing counting methods: {e}")
            return {"error": str(e)}


def format_word_count_result(result: WordCountResult, task_type: str) -> str:
    """
    Format word count result into Persian display text.

    Args:
        result: WordCountResult object
        task_type: IELTS task type

    Returns:
        str: Formatted Persian text
    """
    try:
        task_names = {'task1': 'Task 1', 'task2': 'Task 2'}
        task_name = task_names.get(task_type, task_type)

        # Main count information
        text = f"📊 **تحلیل تعداد کلمات**\n\n"
        text += f"📝 **تسک**: {task_name}\n"
        text += f"🔢 **تعداد کلمات**: {result.total_words}\n"
        text += f"✅ **وضعیت**: {'قابل قبول' if result.is_acceptable else 'نیاز به اصلاح'}\n"
        text += f"🎯 **اعتماد**: {result.confidence_score:.1%}\n\n"

        # Breakdown details
        if result.breakdown:
            text += "📋 **جزئیات شمارش**:\n"
            breakdown = result.breakdown

            if 'regular_words' in breakdown:
                text += f"• کلمات معمولی: {breakdown.get('regular_words', 0)}\n"
            if 'contractions_expanded' in breakdown and breakdown.get('contractions_expanded', 0) > 0:
                text += f"• مخففات گسترش یافته: {breakdown.get('contractions_expanded', 0)}\n"
            if 'hyphenated_words' in breakdown and breakdown.get('hyphenated_words', 0) > 0:
                text += f"• کلمات خط‌دار: {breakdown.get('hyphenated_words', 0)}\n"
            if 'numbers' in breakdown and breakdown.get('numbers', 0) > 0:
                text += f"• اعداد: {breakdown.get('numbers', 0)}\n"

        # Warnings
        if result.warnings:
            text += f"\n⚠️ **هشدارها**:\n"
            for warning in result.warnings:
                text += f"• {warning}\n"

        # Suggestions
        if result.suggestions:
            text += f"\n💡 **پیشنهادات**:\n"
            for suggestion in result.suggestions:
                text += f"• {suggestion}\n"

        return text

    except Exception as e:
        logger.error(f"Error formatting word count result: {e}")
        return f"خطا در نمایش نتایج شمارش کلمات: {str(e)}"


# Global instance
enhanced_word_counter = EnhancedWordCounter()