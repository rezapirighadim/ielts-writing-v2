#!/usr/bin/env python3
"""
Test script for submission system functionality.
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from handlers.text_validators import (
    validate_submission_text,
    TextValidationError,
    count_words,
    check_text_language,
    check_text_quality,
    get_task_requirements_info,
    format_validation_summary,
    get_improvement_suggestions
)


def test_word_counting():
    """Test word counting functionality."""
    print("🔢 Testing word counting...")

    test_cases = [
        ("Hello world", 2),
        ("This is a test.", 4),
        ("", 0),
        ("   Multiple   spaces   between   words   ", 4),
        ("Hello, world! How are you?", 5),
        ("Testing123 word-counting functionality", 3)
    ]

    for text, expected in test_cases:
        result = count_words(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{text}' -> {result} words (expected {expected})")


def test_language_detection():
    """Test language detection functionality."""
    print("\n🌐 Testing language detection...")

    test_cases = [
        ("This is an English text for IELTS testing.", True, "english"),
        ("این متن به زبان فارسی نوشته شده است.", False, "persian"),
        ("This text has both English and فارسی mixed.", False, "mixed"),
        ("12345 !@#$%", False, "unknown")
    ]

    for text, should_be_english, expected_lang in test_cases:
        result = check_text_language(text)
        is_english = result['is_english']
        detected = result['detected_language']

        status = "✅" if is_english == should_be_english else "❌"
        print(f"  {status} '{text[:30]}...' -> English: {is_english}, Detected: {detected}")


def test_text_quality():
    """Test text quality checking."""
    print("\n📝 Testing text quality checking...")

    test_cases = [
        ("This is a good sentence. Here is another one. And a third sentence for testing.", False),
        ("Short.", True),  # Too few sentences
        ("NO CAPITAL LETTERS here.", True),  # No capitals
        ("Testing testing testing testing testing testing.", True)  # Too much repetition
    ]

    for text, should_have_issues in test_cases:
        result = check_text_quality(text)
        has_issues = result['has_issues']

        status = "✅" if has_issues == should_have_issues else "❌"
        issues = ", ".join(result['issues']) if result['issues'] else "None"
        print(f"  {status} '{text[:40]}...' -> Issues: {has_issues} ({issues})")


def test_text_validation():
    """Test complete text validation."""
    print("\n✅ Testing text validation...")

    # Valid Task 2 text
    valid_task2 = """
    In today's modern world, technology has revolutionized the way we communicate and interact with each other. 
    Social media platforms have become an integral part of our daily lives, connecting people across the globe 
    instantaneously. However, this technological advancement has also brought about significant challenges and concerns.

    On one hand, social media has democratized information sharing and has given voice to previously marginalized 
    communities. People can now express their opinions, share their experiences, and connect with like-minded 
    individuals regardless of geographical boundaries. This has led to increased awareness about social issues 
    and has facilitated social movements that have brought about positive change.

    On the other hand, the widespread use of social media has also contributed to the spread of misinformation 
    and has created echo chambers where people only interact with those who share similar views. This can lead 
    to polarization and can hinder constructive dialogue between different groups in society.

    In conclusion, while social media has undoubtedly brought many benefits to our society, it is important 
    that we use these platforms responsibly and critically evaluate the information we encounter online.
    """

    try:
        result = validate_submission_text(valid_task2.strip(), 'task2')
        print(f"  ✅ Valid Task 2 text: {result['word_count']} words - PASSED")
        print(f"     Summary: {result['validation_message']}")
    except TextValidationError as e:
        print(f"  ❌ Valid Task 2 text failed: {e}")

    # Invalid texts
    invalid_cases = [
        ("", "task2", "Empty text"),
        ("Too short", "task2", "Too few words"),
        ("این متن به فارسی است و باید رد شود چون آیلتس انگلیسی است.", "task2", "Persian text"),
        ("Test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test test.",
         "task2", "Too many words")
    ]

    for text, task_type, description in invalid_cases:
        try:
            result = validate_submission_text(text, task_type)
            print(f"  ❌ {description}: Should have failed but passed")
        except TextValidationError as e:
            print(f"  ✅ {description}: Correctly rejected - {e}")


def test_task_requirements():
    """Test task requirements functionality."""
    print("\n📋 Testing task requirements...")

    for task_type in ['task1', 'task2']:
        info = get_task_requirements_info(task_type)
        print(f"  📝 {info['task_name']}: {info['min_words']}-{info['max_words']} words")
        print(f"     Description: {info['description']}")


def test_improvement_suggestions():
    """Test improvement suggestions."""
    print("\n💡 Testing improvement suggestions...")

    short_text = "This is short."
    suggestions = get_improvement_suggestions(short_text, 'task2')

    print(f"  📝 Short text suggestions: {len(suggestions['suggestions'])} found")
    for suggestion in suggestions['suggestions'][:2]:
        print(f"     • {suggestion}")


def run_all_tests():
    """Run all test functions."""
    print("🚀 Starting submission system tests...\n")

    try:
        test_word_counting()
        test_language_detection()
        test_text_quality()
        test_text_validation()
        test_task_requirements()
        test_improvement_suggestions()

        print("\n✅ All tests completed!")

    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()