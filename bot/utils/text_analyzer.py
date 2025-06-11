"""
Text analysis utilities for IELTS submissions.
"""

import re
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from collections import Counter
import statistics

logger = logging.getLogger(__name__)


@dataclass
class TextAnalysisResult:
    """Complete text analysis result."""
    readability_score: float
    sentence_analysis: Dict[str, Any]
    vocabulary_analysis: Dict[str, Any]
    structure_analysis: Dict[str, Any]
    task_specific_analysis: Dict[str, Any]
    overall_quality: str
    recommendations: List[str]


class TextAnalyzer:
    """
    Comprehensive text analyzer for IELTS writing evaluation preparation.

    Python Concept: This class provides detailed text analysis beyond
    simple word counting, helping prepare for AI evaluation.
    """

    def __init__(self):
        # Common academic words for IELTS
        self.academic_words = {
            'analysis', 'approach', 'area', 'assessment', 'assume', 'authority',
            'available', 'benefit', 'concept', 'consistent', 'constitutional',
            'context', 'contract', 'create', 'data', 'definition', 'derived',
            'distribution', 'economic', 'environment', 'established', 'estimate',
            'evidence', 'export', 'factors', 'financial', 'formula', 'function',
            'identified', 'income', 'indicate', 'individual', 'interpretation',
            'involved', 'issues', 'labor', 'legal', 'legislation', 'major',
            'method', 'occur', 'percent', 'period', 'policy', 'principle',
            'procedure', 'process', 'required', 'research', 'response', 'role',
            'section', 'sector', 'significant', 'similar', 'source', 'specific',
            'structure', 'theory', 'variables'
        }

        # Task 1 specific vocabulary
        self.task1_vocabulary = {
            'increase', 'decrease', 'rise', 'fall', 'peak', 'trough', 'plateau',
            'fluctuate', 'remain', 'stable', 'gradual', 'sharp', 'steep',
            'dramatic', 'slight', 'moderate', 'significant', 'proportion',
            'percentage', 'majority', 'minority', 'compare', 'contrast',
            'whereas', 'while', 'although', 'however', 'furthermore', 'moreover'
        }

        # Task 2 specific vocabulary
        self.task2_vocabulary = {
            'argue', 'believe', 'consider', 'suggest', 'propose', 'maintain',
            'conclude', 'assert', 'claim', 'opinion', 'perspective', 'viewpoint',
            'furthermore', 'moreover', 'however', 'nevertheless', 'consequently',
            'therefore', 'thus', 'hence', 'advantage', 'disadvantage', 'benefit',
            'drawback', 'solution', 'problem', 'issue', 'challenge'
        }

        # Transitional phrases
        self.transition_words = {
            'addition': ['furthermore', 'moreover', 'additionally', 'also', 'besides'],
            'contrast': ['however', 'nevertheless', 'nonetheless', 'although', 'whereas'],
            'cause_effect': ['therefore', 'consequently', 'thus', 'hence', 'as a result'],
            'example': ['for example', 'for instance', 'such as', 'namely'],
            'conclusion': ['in conclusion', 'to summarize', 'in summary', 'finally']
        }

    def analyze_sentences(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentence structure and complexity.

        Args:
            text: Input text

        Returns:
            dict: Sentence analysis results
        """
        try:
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]

            if not sentences:
                return {
                    'sentence_count': 0,
                    'average_length': 0,
                    'length_variety': 'none',
                    'complexity_score': 0
                }

            # Calculate sentence lengths
            sentence_lengths = [len(s.split()) for s in sentences]

            # Analyze sentence types
            simple_sentences = 0
            compound_sentences = 0
            complex_sentences = 0

            for sentence in sentences:
                # Simple heuristics for sentence complexity
                if ' and ' in sentence or ' but ' in sentence or ' or ' in sentence:
                    compound_sentences += 1
                elif any(word in sentence.lower() for word in ['because', 'although', 'since', 'while', 'if', 'when']):
                    complex_sentences += 1
                else:
                    simple_sentences += 1

            # Calculate variety metrics
            avg_length = statistics.mean(sentence_lengths)
            length_stdev = statistics.stdev(sentence_lengths) if len(sentence_lengths) > 1 else 0

            # Determine variety level
            if length_stdev < 3:
                variety = 'low'
            elif length_stdev < 6:
                variety = 'medium'
            else:
                variety = 'high'

            # Calculate complexity score
            complexity_score = (compound_sentences + complex_sentences * 1.5) / len(sentences)

            return {
                'sentence_count': len(sentences),
                'average_length': round(avg_length, 1),
                'length_variety': variety,
                'length_stdev': round(length_stdev, 1),
                'simple_sentences': simple_sentences,
                'compound_sentences': compound_sentences,
                'complex_sentences': complex_sentences,
                'complexity_score': round(complexity_score, 2),
                'sentence_lengths': sentence_lengths
            }

        except Exception as e:
            logger.error(f"Error in sentence analysis: {e}")
            return {'error': str(e)}

    def analyze_vocabulary(self, text: str, task_type: str) -> Dict[str, Any]:
        """
        Analyze vocabulary usage and appropriateness.

        Args:
            text: Input text
            task_type: IELTS task type

        Returns:
            dict: Vocabulary analysis results
        """
        try:
            # Clean and tokenize
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

            if not words:
                return {'error': 'No words found'}

            # Basic statistics
            unique_words = set(words)
            word_counts = Counter(words)

            # Lexical diversity (Type-Token Ratio)
            lexical_diversity = len(unique_words) / len(words)

            # Academic vocabulary usage
            academic_words_used = unique_words.intersection(self.academic_words)
            academic_ratio = len(academic_words_used) / len(unique_words)

            # Task-specific vocabulary
            task_vocab = self.task1_vocabulary if task_type == 'task1' else self.task2_vocabulary
            task_words_used = unique_words.intersection(task_vocab)
            task_vocab_ratio = len(task_words_used) / len(unique_words)

            # Transition words analysis
            transition_usage = {}
            total_transitions = 0

            for category, transitions in self.transition_words.items():
                found_transitions = []
                for transition in transitions:
                    if transition in text.lower():
                        found_transitions.append(transition)
                        total_transitions += 1
                transition_usage[category] = found_transitions

            # Word frequency analysis
            most_common = word_counts.most_common(10)
            repetitive_words = [word for word, count in most_common if count > max(3, len(words) * 0.05)]

            return {
                'total_words': len(words),
                'unique_words': len(unique_words),
                'lexical_diversity': round(lexical_diversity, 3),
                'academic_words_count': len(academic_words_used),
                'academic_ratio': round(academic_ratio, 3),
                'task_specific_words': len(task_words_used),
                'task_vocab_ratio': round(task_vocab_ratio, 3),
                'transition_words_used': total_transitions,
                'transition_categories': transition_usage,
                'repetitive_words': repetitive_words,
                'most_common_words': most_common[:5]
            }

        except Exception as e:
            logger.error(f"Error in vocabulary analysis: {e}")
            return {'error': str(e)}

    def analyze_text_structure(self, text: str, task_type: str) -> Dict[str, Any]:
        """
        Analyze text structure and organization.

        Args:
            text: Input text
            task_type: IELTS task type

        Returns:
            dict: Structure analysis results
        """
        try:
            # Split into paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

            # If no paragraph breaks, try to identify by length
            if len(paragraphs) == 1:
                sentences = re.split(r'[.!?]+', text)
                sentences = [s.strip() for s in sentences if s.strip()]

                # Estimate paragraphs based on sentence grouping
                if len(sentences) > 6:
                    paragraphs = []
                    current_para = []
                    for i, sentence in enumerate(sentences):
                        current_para.append(sentence)
                        if (i + 1) % 3 == 0 or i == len(sentences) - 1:
                            paragraphs.append(' '.join(current_para))
                            current_para = []

            # Analyze paragraph structure
            paragraph_lengths = [len(p.split()) for p in paragraphs]

            # Check for introduction and conclusion patterns
            has_introduction = False
            has_conclusion = False

            if paragraphs:
                # Introduction indicators
                intro_indicators = ['in today', 'nowadays', 'recently', 'it is', 'this essay']
                first_para = paragraphs[0].lower()
                has_introduction = any(indicator in first_para for indicator in intro_indicators)

                # Conclusion indicators
                conclusion_indicators = ['in conclusion', 'to conclude', 'in summary', 'finally', 'to summarize']
                last_para = paragraphs[-1].lower()
                has_conclusion = any(indicator in last_para for indicator in conclusion_indicators)

            # Task-specific structure analysis
            task_structure_score = 0

            if task_type == 'task1':
                # Task 1 should have: introduction, overview, detailed paragraphs
                if len(paragraphs) >= 3:
                    task_structure_score += 0.3
                if has_introduction:
                    task_structure_score += 0.3
                # Check for overview (key features mentioned)
                overview_words = ['overall', 'main', 'key', 'significant', 'notable']
                if any(word in text.lower() for word in overview_words):
                    task_structure_score += 0.4

            elif task_type == 'task2':
                # Task 2 should have: introduction, body paragraphs, conclusion
                if len(paragraphs) >= 4:
                    task_structure_score += 0.3
                if has_introduction:
                    task_structure_score += 0.3
                if has_conclusion:
                    task_structure_score += 0.4

            return {
                'paragraph_count': len(paragraphs),
                'paragraph_lengths': paragraph_lengths,
                'average_paragraph_length': round(statistics.mean(paragraph_lengths), 1) if paragraph_lengths else 0,
                'has_introduction': has_introduction,
                'has_conclusion': has_conclusion,
                'structure_score': round(task_structure_score, 2),
                'structure_quality': 'good' if task_structure_score >= 0.7 else 'fair' if task_structure_score >= 0.4 else 'needs_improvement'
            }

        except Exception as e:
            logger.error(f"Error in structure analysis: {e}")
            return {'error': str(e)}

    def calculate_readability_score(self, text: str) -> float:
        """
        Calculate a simplified readability score.

        Args:
            text: Input text

        Returns:
            float: Readability score (0-100, higher is more readable)
        """
        try:
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]

            words = re.findall(r'\b[a-zA-Z]+\b', text)

            if not sentences or not words:
                return 0

            # Calculate metrics
            avg_sentence_length = len(words) / len(sentences)

            # Count syllables (simplified estimation)
            syllable_count = 0
            for word in words:
                syllables = max(1, len(re.findall(r'[aeiouAEIOU]', word)))
                syllable_count += syllables

            avg_syllables_per_word = syllable_count / len(words)

            # Simplified Flesch Reading Ease formula
            readability = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)

            # Normalize to 0-100
            return max(0, min(100, readability))

        except Exception as e:
            logger.error(f"Error calculating readability: {e}")
            return 0

    def get_improvement_recommendations(self, analysis_results: Dict[str, Any], task_type: str) -> List[str]:
        """
        Generate improvement recommendations based on analysis.

        Args:
            analysis_results: Combined analysis results
            task_type: IELTS task type

        Returns:
            List of recommendation strings in Persian
        """
        recommendations = []

        try:
            # Sentence analysis recommendations
            if 'sentence_analysis' in analysis_results:
                sentence_data = analysis_results['sentence_analysis']

                if sentence_data.get('complexity_score', 0) < 0.3:
                    recommendations.append("از جملات پیچیده‌تر استفاده کنید (because, although, however)")

                if sentence_data.get('length_variety') == 'low':
                    recommendations.append("تنوع در طول جملات را افزایش دهید")

            # Vocabulary recommendations
            if 'vocabulary_analysis' in analysis_results:
                vocab_data = analysis_results['vocabulary_analysis']

                if vocab_data.get('lexical_diversity', 0) < 0.5:
                    recommendations.append("تنوع واژگان را افزایش دهید و از تکرار کلمات خودداری کنید")

                if vocab_data.get('academic_ratio', 0) < 0.1:
                    recommendations.append("از واژگان آکادمیک بیشتری استفاده کنید")

                if vocab_data.get('task_vocab_ratio', 0) < 0.05:
                    if task_type == 'task1':
                        recommendations.append("از واژگان تخصصی توصیف داده استفاده کنید (increase, decrease, peak)")
                    else:
                        recommendations.append("از واژگان نظری و بحثی استفاده کنید (argue, believe, consider)")

                if vocab_data.get('transition_words_used', 0) < 3:
                    recommendations.append("از کلمات ربط بیشتری استفاده کنید (however, furthermore, therefore)")

            # Structure recommendations
            if 'structure_analysis' in analysis_results:
                structure_data = analysis_results['structure_analysis']

                if structure_data.get('paragraph_count', 0) < 3:
                    recommendations.append("متن را به پاراگراف‌های مجزا تقسیم کنید")

                if not structure_data.get('has_introduction', False):
                    recommendations.append("یک مقدمه مناسب برای متن بنویسید")

                if task_type == 'task2' and not structure_data.get('has_conclusion', False):
                    recommendations.append("یک نتیجه‌گیری مناسب اضافه کنید")

            # Readability recommendations
            readability = analysis_results.get('readability_score', 0)
            if readability < 30:
                recommendations.append("جملات را ساده‌تر و قابل فهم‌تر بنویسید")
            elif readability > 80:
                recommendations.append("از جملات پیچیده‌تر برای نشان دادن مهارت زبانی استفاده کنید")

            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["خطا در تولید پیشنهادات بهبود"]

    def perform_complete_analysis(self, text: str, task_type: str) -> TextAnalysisResult:
        """
        Perform complete text analysis.

        Args:
            text: Input text
            task_type: IELTS task type

        Returns:
            TextAnalysisResult: Complete analysis result
        """
        try:
            # Perform individual analyses
            sentence_analysis = self.analyze_sentences(text)
            vocabulary_analysis = self.analyze_vocabulary(text, task_type)
            structure_analysis = self.analyze_text_structure(text, task_type)
            readability_score = self.calculate_readability_score(text)

            # Task-specific analysis
            task_specific = {}
            if task_type == 'task1':
                # Check for data description elements
                data_words = ['increase', 'decrease', 'peak', 'trough', 'percentage', 'proportion']
                found_data_words = sum(1 for word in data_words if word in text.lower())
                task_specific = {
                    'data_vocabulary_count': found_data_words,
                    'has_overview': any(word in text.lower() for word in ['overall', 'main', 'key']),
                    'has_comparisons': any(word in text.lower() for word in ['higher', 'lower', 'compared'])
                }
            else:  # task2
                # Check for argumentative elements
                opinion_words = ['believe', 'think', 'opinion', 'argue', 'suggest']
                found_opinion_words = sum(1 for word in opinion_words if word in text.lower())
                task_specific = {
                    'opinion_vocabulary_count': found_opinion_words,
                    'has_clear_position': any(
                        phrase in text.lower() for phrase in ['i believe', 'in my opinion', 'i think']),
                    'has_examples': 'for example' in text.lower() or 'for instance' in text.lower()
                }

            # Combine all analyses
            combined_results = {
                'sentence_analysis': sentence_analysis,
                'vocabulary_analysis': vocabulary_analysis,
                'structure_analysis': structure_analysis,
                'readability_score': readability_score,
                'task_specific_analysis': task_specific
            }

            # Generate recommendations
            recommendations = self.get_improvement_recommendations(combined_results, task_type)

            # Calculate overall quality
            quality_scores = []

            if sentence_analysis.get('complexity_score', 0) > 0:
                quality_scores.append(min(100, sentence_analysis['complexity_score'] * 100))

            if vocabulary_analysis.get('lexical_diversity', 0) > 0:
                quality_scores.append(vocabulary_analysis['lexical_diversity'] * 100)

            if structure_analysis.get('structure_score', 0) > 0:
                quality_scores.append(structure_analysis['structure_score'] * 100)

            quality_scores.append(readability_score)

            overall_score = statistics.mean(quality_scores) if quality_scores else 0

            if overall_score >= 80:
                overall_quality = "excellent"
            elif overall_score >= 65:
                overall_quality = "good"
            elif overall_score >= 50:
                overall_quality = "fair"
            else:
                overall_quality = "needs_improvement"

            return TextAnalysisResult(
                readability_score=readability_score,
                sentence_analysis=sentence_analysis,
                vocabulary_analysis=vocabulary_analysis,
                structure_analysis=structure_analysis,
                task_specific_analysis=task_specific,
                overall_quality=overall_quality,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Error in complete text analysis: {e}")
            return TextAnalysisResult(
                readability_score=0,
                sentence_analysis={},
                vocabulary_analysis={},
                structure_analysis={},
                task_specific_analysis={},
                overall_quality="error",
                recommendations=["خطا در تحلیل متن"]
            )


def format_analysis_summary(analysis: TextAnalysisResult, task_type: str) -> str:
    """
    Format complete analysis into Persian summary.

    Args:
        analysis: TextAnalysisResult object
        task_type: IELTS task type

    Returns:
        str: Formatted Persian summary
    """
    try:
        task_names = {'task1': 'Task 1', 'task2': 'Task 2'}
        task_name = task_names.get(task_type, task_type)

        quality_translations = {
            'excellent': 'عالی',
            'good': 'خوب',
            'fair': 'متوسط',
            'needs_improvement': 'نیاز به بهبود',
            'error': 'خطا'
        }

        summary = f"""📋 **تحلیل کامل متن**

📝 **نوع تسک**: {task_name}
🏆 **کیفیت کلی**: {quality_translations.get(analysis.overall_quality, analysis.overall_quality)}
📖 **خوانایی**: {analysis.readability_score:.0f}/100

📊 **تحلیل جملات**:"""

        if analysis.sentence_analysis:
            sent = analysis.sentence_analysis
            summary += f"""
• تعداد جملات: {sent.get('sentence_count', 0)}
• طول متوسط: {sent.get('average_length', 0)} کلمه
• تنوع طول: {sent.get('length_variety', 'نامشخص')}
• پیچیدگی: {sent.get('complexity_score', 0):.1f}/1.0"""

        summary += f"\n\n📚 **تحلیل واژگان**:"
        if analysis.vocabulary_analysis:
            vocab = analysis.vocabulary_analysis
            summary += f"""
• تنوع واژگان: {vocab.get('lexical_diversity', 0):.1%}
• واژگان آکادمیک: {vocab.get('academic_words_count', 0)}
• کلمات ربط: {vocab.get('transition_words_used', 0)}"""

        summary += f"\n\n🏗️ **ساختار متن**:"
        if analysis.structure_analysis:
            struct = analysis.structure_analysis
            summary += f"""
• تعداد پاراگراف: {struct.get('paragraph_count', 0)}
• مقدمه: {'✅' if struct.get('has_introduction', False) else '❌'}
• نتیجه‌گیری: {'✅' if struct.get('has_conclusion', False) else '❌'}
• امتیاز ساختار: {struct.get('structure_score', 0):.1f}/1.0"""

        if analysis.recommendations:
            summary += f"\n\n💡 **پیشنهادات بهبود**:\n"
            for i, rec in enumerate(analysis.recommendations[:5], 1):
                summary += f"{i}. {rec}\n"

        return summary

    except Exception as e:
        logger.error(f"Error formatting analysis summary: {e}")
        return "خطا در نمایش تحلیل متن"


# Global instance
text_analyzer = TextAnalyzer()