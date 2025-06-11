#!/usr/bin/env python3
"""
Test script for enhanced word count validation and text analysis.
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from handlers.word_count_validator import (
    enhanced_word_counter,
    format_word_count_result,
    WordCountMethod
)
from utils.text_analyzer import text_analyzer, format_analysis_summary


def test_enhanced_word_counting():
    """Test enhanced word counting methods."""
    print("🔢 Testing enhanced word counting...")

    test_cases = [
        "Hello world",
        "Don't you think we can't solve this problem?",
        "The well-known scientist studied DNA sequences in 2024.",
        "I'll be there at 3:30 PM, won't I?",
        "The COVID-19 pandemic affected millions of people worldwide."
    ]

    for text in test_cases:
        print(f"\n📝 Text: '{text}'")

        # Test all methods
        simple_count, simple_breakdown = enhanced_word_counter.count_words_simple(text)
        regex_count, regex_breakdown = enhanced_word_counter.count_words_regex(text)
        advanced_count, advanced_breakdown = enhanced_word_counter.count_words_advanced(text)

        print(f"   Simple: {simple_count} words")
        print(f"   Regex: {regex_count} words")
        print(f"   Advanced: {advanced_count} words")
        print(f"   Contractions expanded: {advanced_breakdown.get('contractions_expanded', 0)}")
        print(f"   Hyphenated words: {advanced_breakdown.get('hyphenated_words', 0)}")


def test_word_count_validation():
    """Test complete word count validation."""
    print("\n✅ Testing word count validation...")

    # Valid Task 2 text
    task2_text = """
    Technology has fundamentally transformed the way we communicate in the modern era. 
    Social media platforms have connected billions of people worldwide, enabling instant 
    communication across geographical boundaries. However, this technological revolution 
    has also introduced significant challenges that society must address.

    On one hand, digital communication has democratized information sharing and given 
    voice to previously marginalized communities. People can now express their opinions, 
    share experiences, and mobilize support for important causes more effectively than 
    ever before. This has led to increased awareness about social issues and has 
    facilitated grassroots movements that have brought about positive change.

    On the other hand, the proliferation of digital communication has also contributed 
    to the spread of misinformation and has created echo chambers where people only 
    interact with those who share similar viewpoints. This polarization can hinder 
    constructive dialogue and compromise democratic processes.

    In conclusion, while digital communication technologies have undoubtedly brought 
    many benefits to society, it is crucial that we develop strategies to mitigate 
    their negative effects and ensure they contribute to a more informed and connected world.
    """

    result = enhanced_word_counter.validate_word_count(task2_text.strip(), 'task2')

    print(f"✅ Task 2 validation:")
    print(f"   Word count: {result.total_words}")
    print(f"   Acceptable: {result.is_acceptable}")
    print(f"   Confidence: {result.confidence_score:.1%}")
    print(f"   Method: {result.method_used}")

    if result.warnings:
        print(f"   Warnings: {result.warnings}")
    if result.suggestions:
        print(f"   Suggestions: {result.suggestions}")

    # Test formatting
    formatted_result = format_word_count_result(result, 'task2')
    print(f"\n📋 Formatted result:\n{formatted_result}")


def test_text_analysis():
    """Test comprehensive text analysis."""
    print("\n📊 Testing text analysis...")

    # Sample Task 2 text for analysis
    sample_text = """
    In today's rapidly evolving world, the debate about whether technology enhances or 
    diminishes human relationships has become increasingly relevant. While some argue 
    that digital communication tools have brought people closer together, others believe 
    that technology has created barriers to genuine human connection.

    Proponents of technology argue that digital platforms have revolutionized the way 
    we maintain relationships. For example, social media allows families separated by 
    vast distances to stay connected through regular updates and video calls. Furthermore, 
    online communities enable people with shared interests to form meaningful connections 
    regardless of geographical constraints.

    However, critics contend that technology has led to superficial interactions and 
    reduced face-to-face communication. They argue that the quality of relationships 
    has deteriorated because people rely too heavily on digital mediums, which lack 
    the emotional depth of in-person conversations.

    In conclusion, while technology has undoubtedly expanded our ability to connect 
    with others, it is essential that we maintain a balance between digital and 
    real-world interactions to preserve the authenticity of human relationships.
    """

    # Perform analysis
    analysis = text_analyzer.perform_complete_analysis(sample_text.strip(), 'task2')

    print(f"📖 Readability score: {analysis.readability_score:.1f}")
    print(f"🏆 Overall quality: {analysis.overall_quality}")

    # Sentence analysis
    if analysis.sentence_analysis:
        sent = analysis.sentence_analysis
        print(f"\n📝 Sentence analysis:")
        print(f"   Count: {sent.get('sentence_count', 0)}")
        print(f"   Average length: {sent.get('average_length', 0)} words")
        print(f"   Complexity score: {sent.get('complexity_score', 0):.2f}")
        print(f"   Complex sentences: {sent.get('complex_sentences', 0)}")

    # Vocabulary analysis
    if analysis.vocabulary_analysis:
        vocab = analysis.vocabulary_analysis
        print(f"\n📚 Vocabulary analysis:")
        print(f"   Lexical diversity: {vocab.get('lexical_diversity', 0):.1%}")
        print(f"   Academic words: {vocab.get('academic_words_count', 0)}")
        print(f"   Transition words: {vocab.get('transition_words_used', 0)}")

    # Structure analysis
    if analysis.structure_analysis:
        struct = analysis.structure_analysis
        print(f"\n🏗️ Structure analysis:")
        print(f"   Paragraphs: {struct.get('paragraph_count', 0)}")
        print(f"   Has introduction: {struct.get('has_introduction', False)}")
        print(f"   Has conclusion: {struct.get('has_conclusion', False)}")
        print(f"   Structure score: {struct.get('structure_score', 0):.2f}")

    # Task-specific analysis
    if analysis.task_specific_analysis:
        task_spec = analysis.task_specific_analysis
        print(f"\n🎯 Task 2 specific:")
        print(f"   Opinion vocabulary: {task_spec.get('opinion_vocabulary_count', 0)}")
        print(f"   Clear position: {task_spec.get('has_clear_position', False)}")
        print(f"   Has examples: {task_spec.get('has_examples', False)}")

    # Recommendations
    if analysis.recommendations:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(analysis.recommendations[:3], 1):
            print(f"   {i}. {rec}")

    # Test formatted summary
    formatted_analysis = format_analysis_summary(analysis, 'task2')
    print(f"\n📋 Formatted analysis:\n{formatted_analysis}")


def test_method_comparison():
    """Test comparison of different counting methods."""
    print("\n🔍 Testing method comparison...")

    test_text = "I can't believe we're studying COVID-19's impact on twenty-first-century education."

    comparison = enhanced_word_counter.compare_counting_methods(test_text)

    print(f"📝 Text: '{test_text}'")
    print(f"📊 Method comparison:")

    for method, data in comparison['methods'].items():
        print(f"   {method}: {data['count']} words")

    print(f"   Variance: {comparison['variance']}")
    print(f"   Recommended: {comparison['recommended_count']}")
    print(f"   Agreement: {comparison['agreement_level']}")


def test_edge_cases():
    """Test edge cases and potential issues."""
    print("\n⚠️ Testing edge cases...")

    edge_cases = [
        ("", "Empty text"),
        ("   ", "Whitespace only"),
        ("123 456 789", "Numbers only"),
        ("!!!! @@@@ ####", "Symbols only"),
        ("a b c d e f g h i j", "Single letters"),
        ("very very very very very very very very very repetitive", "Highly repetitive"),
        ("این متن فارسی است", "Persian text"),
        ("Mixed English و فارسی text", "Mixed languages")
    ]

    for text, description in edge_cases:
        try:
            result = enhanced_word_counter.validate_word_count(text, 'task2')
            status = "✅ Pass" if result.is_acceptable else "❌ Fail"
            print(f"   {status} {description}: {result.total_words} words, {len(result.warnings)} warnings")
        except Exception as e:
            print(f"   ⚠️ {description}: Error - {e}")


def test_task1_vs_task2():
    """Test different requirements for Task 1 vs Task 2."""
    print("\n📋 Testing Task 1 vs Task 2 requirements...")

    # Task 1 text (should be around 150 words)
    task1_text = """
    The chart illustrates the changes in population growth rates across four major 
    cities between 2000 and 2020. Overall, while some cities experienced significant 
    growth, others showed declining populations during this period.

    New York demonstrated the highest growth rate, increasing from 8.2 million to 
    10.5 million residents. Similarly, Tokyo showed steady growth from 12.1 million 
    to 14.2 million inhabitants. In contrast, London's population remained relatively 
    stable, fluctuating between 7.8 and 8.1 million throughout the two-decade period.

    Most notably, Detroit experienced a dramatic decline, with its population falling 
    from 2.1 million in 2000 to just 1.3 million in 2020, representing the steepest 
    decrease among all cities examined.
    """

    # Task 2 text (should be around 250+ words)
    task2_text = """
    The increasing prevalence of remote work has fundamentally altered traditional 
    employment patterns and workplace dynamics. While this shift offers numerous 
    advantages for both employees and employers, it also presents significant challenges 
    that organizations must carefully consider.

    From an employee perspective, remote work provides unprecedented flexibility and 
    work-life balance. Workers can eliminate lengthy commutes, reduce transportation 
    costs, and create personalized work environments that enhance productivity. 
    Furthermore, remote work enables companies to access talent from global markets, 
    breaking down geographical barriers that previously limited hiring options.

    However, remote work also introduces substantial challenges. Many employees struggle 
    with isolation and reduced collaboration opportunities, which can negatively impact 
    creativity and team cohesion. Additionally, the blurred boundaries between work 
    and personal life can lead to longer working hours and increased stress levels.

    In conclusion, while remote work represents a significant evolution in employment 
    practices, organizations must implement comprehensive strategies to maximize its 
    benefits while addressing its inherent limitations to ensure long-term success.
    """

    # Test both tasks
    task1_result = enhanced_word_counter.validate_word_count(task1_text.strip(), 'task1')
    task2_result = enhanced_word_counter.validate_word_count(task2_text.strip(), 'task2')

    print(f"📊 Task 1 result:")
    print(f"   Words: {task1_result.total_words} (target: 150-200)")
    print(f"   Acceptable: {task1_result.is_acceptable}")

    print(f"\n📝 Task 2 result:")
    print(f"   Words: {task2_result.total_words} (target: 250-350)")
    print(f"   Acceptable: {task2_result.is_acceptable}")


def run_all_tests():
    """Run all enhanced validation tests."""
    print("🚀 Starting enhanced word count and text analysis tests...\n")

    try:
        test_enhanced_word_counting()
        test_word_count_validation()
        test_text_analysis()
        test_method_comparison()
        test_edge_cases()
        test_task1_vs_task2()

        print("\n✅ All enhanced validation tests completed!")
        print("\n📊 Summary:")
        print("   • Enhanced word counting with contraction expansion")
        print("   • Comprehensive text analysis with readability scoring")
        print("   • Task-specific vocabulary analysis")
        print("   • Structure and coherence evaluation")
        print("   • Detailed Persian feedback and recommendations")

    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()