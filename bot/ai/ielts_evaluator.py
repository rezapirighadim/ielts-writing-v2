"""
IELTS writing evaluator that integrates AI evaluation with submission processing.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from ai.openai_client import get_openai_client, AIEvaluationResult
from database.enhanced_submission_operations import EnhancedSubmissionOperations
from handlers.text_validators import validate_submission_text, get_enhanced_validation_summary
from handlers.word_count_validator import enhanced_word_counter, format_word_count_result
from utils.text_analyzer import text_analyzer, format_analysis_summary

logger = logging.getLogger(__name__)


class IELTSEvaluator:
    """
    Complete IELTS writing evaluator that combines validation, analysis, and AI evaluation.

    Python Concept: This class orchestrates the entire evaluation pipeline
    from text validation through AI evaluation to result storage.
    """

    def __init__(self):
        self.openai_client = None
        self._initialize_ai_client()

    def _initialize_ai_client(self):
        """Initialize OpenAI client."""
        try:
            self.openai_client = get_openai_client()
            logger.info("✅ IELTS Evaluator initialized with AI client")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI client: {e}")
            self.openai_client = None

    async def evaluate_submission(self, submission_id: int) -> Dict[str, Any]:
        """
        Perform complete evaluation of a submission.

        Args:
            submission_id: Database submission ID

        Returns:
            dict: Complete evaluation results
        """
        try:
            # Get submission data
            submission_data = EnhancedSubmissionOperations.get_submission_with_analysis(submission_id)
            if not submission_data:
                return {
                    "success": False,
                    "error": "submission_not_found",
                    "message": "ارسال یافت نشد"
                }

            logger.info(f"Starting evaluation for submission {submission_id}")

            # Extract submission details
            text = submission_data['submission_text']
            task_type = submission_data['task_type']
            word_count = submission_data['word_count']

            # Prepare additional context for AI
            additional_context = {
                'word_count': word_count,
                'character_count': submission_data.get('character_count', 0),
                'submission_id': submission_id,
                'validation_data': submission_data.get('validation_data', {}),
                'analysis_metadata': submission_data.get('analysis_metadata', {})
            }

            # Add readability and quality scores if available
            analysis_metadata = submission_data.get('analysis_metadata', {})
            if analysis_metadata:
                additional_context.update({
                    'readability_score': analysis_metadata.get('readability_score', 0),
                    'overall_quality': analysis_metadata.get('overall_quality', 'unknown'),
                    'lexical_diversity': analysis_metadata.get('lexical_diversity', 0),
                    'complexity_score': analysis_metadata.get('complexity_score', 0),
                    'structure_score': analysis_metadata.get('structure_score', 0)
                })

            # Perform AI evaluation
            ai_result = await self._perform_ai_evaluation(text, task_type, additional_context)

            if not ai_result.success:
                return {
                    "success": False,
                    "error": "ai_evaluation_failed",
                    "message": f"خطا در ارزیابی AI: {ai_result.error_message}",
                    "submission_id": submission_id
                }

            # Prepare analysis data for storage
            analysis_data = {
                'submission_id': submission_id,
                'task_achievement_score': ai_result.task_achievement_score,
                'coherence_cohesion_score': ai_result.coherence_cohesion_score,
                'lexical_resource_score': ai_result.lexical_resource_score,
                'grammatical_accuracy_score': ai_result.grammatical_accuracy_score,
                'overall_score': ai_result.overall_score,
                'feedback_text': ai_result.feedback_text,
                'processing_time_seconds': ai_result.processing_time_seconds,
                'status': 'completed',
                'ai_model_version': ai_result.model_version,
                'detailed_feedback': {
                    'strengths': ai_result.strengths or [],
                    'weaknesses': ai_result.weaknesses or [],
                    'improvement_suggestions': ai_result.improvement_suggestions or []
                },
                'scoring_breakdown': {
                    'task_achievement': {
                        'score': ai_result.task_achievement_score,
                        'description': 'Task fulfillment and response completeness'
                    },
                    'coherence_cohesion': {
                        'score': ai_result.coherence_cohesion_score,
                        'description': 'Organization and logical flow'
                    },
                    'lexical_resource': {
                        'score': ai_result.lexical_resource_score,
                        'description': 'Vocabulary range and accuracy'
                    },
                    'grammatical_accuracy': {
                        'score': ai_result.grammatical_accuracy_score,
                        'description': 'Grammar range and accuracy'
                    }
                },
                'tokens_used': ai_result.tokens_used
            }

            # Update submission with AI analysis
            success = EnhancedSubmissionOperations.update_submission_analysis(submission_id, analysis_data)

            if not success:
                return {
                    "success": False,
                    "error": "storage_failed",
                    "message": "خطا در ذخیره نتایج ارزیابی",
                    "ai_result": ai_result,
                    "submission_id": submission_id
                }

            logger.info(f"✅ Evaluation completed for submission {submission_id} - Score: {ai_result.overall_score}")

            return {
                "success": True,
                "submission_id": submission_id,
                "overall_score": ai_result.overall_score,
                "scores": {
                    "task_achievement": ai_result.task_achievement_score,
                    "coherence_cohesion": ai_result.coherence_cohesion_score,
                    "lexical_resource": ai_result.lexical_resource_score,
                    "grammatical_accuracy": ai_result.grammatical_accuracy_score
                },
                "feedback": ai_result.feedback_text,
                "strengths": ai_result.strengths,
                "weaknesses": ai_result.weaknesses,
                "suggestions": ai_result.improvement_suggestions,
                "processing_time": ai_result.processing_time_seconds,
                "tokens_used": ai_result.tokens_used,
                "message": f"ارزیابی با موفقیت انجام شد - نمره کلی: {ai_result.overall_score}"
            }

        except Exception as e:
            logger.error(f"❌ Error in submission evaluation: {e}")
            return {
                "success": False,
                "error": "evaluation_exception",
                "message": f"خطای غیرمنتظره در ارزیابی: {str(e)}",
                "submission_id": submission_id
            }

    async def _perform_ai_evaluation(self, text: str, task_type: str,
                                     additional_context: Dict[str, Any]) -> AIEvaluationResult:
        """
        Perform AI evaluation with proper error handling.

        Args:
            text: Text to evaluate
            task_type: IELTS task type
            additional_context: Additional context data

        Returns:
            AIEvaluationResult: AI evaluation result
        """
        try:
            if not self.openai_client:
                return AIEvaluationResult(
                    success=False,
                    error_message="OpenAI client not initialized"
                )

            # Perform evaluation
            result = await self.openai_client.evaluate_ielts_writing(
                text=text,
                task_type=task_type,
                additional_context=additional_context
            )

            return result

        except Exception as e:
            logger.error(f"AI evaluation error: {e}")
            return AIEvaluationResult(
                success=False,
                error_message=str(e)
            )

    async def quick_evaluate_text(self, text: str, task_type: str) -> Dict[str, Any]:
        """
        Quick evaluation without storing in database (for testing/preview).

        Args:
            text: Text to evaluate
            task_type: IELTS task type

        Returns:
            dict: Evaluation results
        """
        try:
            # Quick validation
            try:
                validation_result = validate_submission_text(text, task_type)
            except Exception as e:
                return {
                    "success": False,
                    "error": "validation_failed",
                    "message": f"خطا در اعتبارسنجی: {str(e)}"
                }

            # Prepare context
            additional_context = {
                'word_count': validation_result['word_count'],
                'character_count': validation_result['character_count'],
                'validation_method': 'quick_evaluation'
            }

            # Get analysis data if available
            text_analysis = validation_result.get('text_analysis')
            if text_analysis and hasattr(text_analysis, 'readability_score'):
                additional_context['readability_score'] = text_analysis.readability_score
                additional_context['overall_quality'] = text_analysis.overall_quality

            # Perform AI evaluation
            ai_result = await self._perform_ai_evaluation(text, task_type, additional_context)

            if not ai_result.success:
                return {
                    "success": False,
                    "error": "ai_evaluation_failed",
                    "message": f"خطا در ارزیابی: {ai_result.error_message}"
                }

            return {
                "success": True,
                "overall_score": ai_result.overall_score,
                "scores": {
                    "task_achievement": ai_result.task_achievement_score,
                    "coherence_cohesion": ai_result.coherence_cohesion_score,
                    "lexical_resource": ai_result.lexical_resource_score,
                    "grammatical_accuracy": ai_result.grammatical_accuracy_score
                },
                "feedback": ai_result.feedback_text,
                "strengths": ai_result.strengths,
                "weaknesses": ai_result.weaknesses,
                "suggestions": ai_result.improvement_suggestions,
                "word_count": validation_result['word_count'],
                "processing_time": ai_result.processing_time_seconds,
                "message": f"ارزیابی سریع - نمره کلی: {ai_result.overall_score}"
            }

        except Exception as e:
            logger.error(f"Quick evaluation error: {e}")
            return {
                "success": False,
                "error": "quick_evaluation_exception",
                "message": f"خطا در ارزیابی سریع: {str(e)}"
            }

    def format_evaluation_result(self, evaluation_result: Dict[str, Any]) -> str:
        """
        Format evaluation result for display.

        Args:
            evaluation_result: Evaluation result dictionary

        Returns:
            str: Formatted Persian text
        """
        try:
            if not evaluation_result.get("success", False):
                return f"❌ خطا در ارزیابی: {evaluation_result.get('message', 'نامشخص')}"

            overall_score = evaluation_result.get("overall_score", 0)
            scores = evaluation_result.get("scores", {})
            feedback = evaluation_result.get("feedback", "")
            processing_time = evaluation_result.get("processing_time", 0)

            # Format scores
            score_text = f"""🎯 **نمره کلی آیلتس: {overall_score}/9**

📊 **جزئیات نمرات**:
• Task Achievement: {scores.get('task_achievement', 0)}/9
• Coherence & Cohesion: {scores.get('coherence_cohesion', 0)}/9  
• Lexical Resource: {scores.get('lexical_resource', 0)}/9
• Grammatical Accuracy: {scores.get('grammatical_accuracy', 0)}/9

💬 **بازخورد کلی**:
{feedback}"""

            # Add strengths
            strengths = evaluation_result.get("strengths", [])
            if strengths:
                score_text += f"\n\n💪 **نقاط قوت**:\n"
                for i, strength in enumerate(strengths, 1):
                    score_text += f"{i}. {strength}\n"

            # Add weaknesses
            weaknesses = evaluation_result.get("weaknesses", [])
            if weaknesses:
                score_text += f"\n⚠️ **نقاط ضعف**:\n"
                for i, weakness in enumerate(weaknesses, 1):
                    score_text += f"{i}. {weakness}\n"

            # Add suggestions
            suggestions = evaluation_result.get("suggestions", [])
            if suggestions:
                score_text += f"\n💡 **پیشنهادات بهبود**:\n"
                for i, suggestion in enumerate(suggestions, 1):
                    score_text += f"{i}. {suggestion}\n"

            # Add processing info
            score_text += f"\n⏱️ **زمان پردازش**: {processing_time} ثانیه"

            return score_text

        except Exception as e:
            logger.error(f"Error formatting evaluation result: {e}")
            return "خطا در نمایش نتایج ارزیابی"

    def is_ai_available(self) -> bool:
        """
        Check if AI evaluation is available.

        Returns:
            bool: True if AI client is ready, False otherwise
        """
        return self.openai_client is not None

    def get_evaluation_stats(self) -> Dict[str, Any]:
        """
        Get evaluation system statistics.

        Returns:
            dict: System statistics
        """
        try:
            stats = {
                "ai_client_available": self.is_ai_available(),
                "openai_model": self.openai_client.model if self.openai_client else None,
                "system_status": "ready" if self.is_ai_available() else "ai_unavailable"
            }

            if self.openai_client:
                stats.update(self.openai_client.get_api_usage_stats())

            return stats

        except Exception as e:
            logger.error(f"Error getting evaluation stats: {e}")
            return {
                "ai_client_available": False,
                "system_status": "error",
                "error": str(e)
            }


# Global IELTS evaluator instance
_ielts_evaluator: Optional[IELTSEvaluator] = None


def get_ielts_evaluator() -> IELTSEvaluator:
    """
    Get or create global IELTS evaluator instance.

    Returns:
        IELTSEvaluator: Configured IELTS evaluator
    """
    global _ielts_evaluator

    if _ielts_evaluator is None:
        _ielts_evaluator = IELTSEvaluator()

    return _ielts_evaluator


async def evaluate_submission_async(submission_id: int) -> Dict[str, Any]:
    """
    Async wrapper for submission evaluation.

    Args:
        submission_id: Submission ID to evaluate

    Returns:
        dict: Evaluation results
    """
    try:
        evaluator = get_ielts_evaluator()
        return await evaluator.evaluate_submission(submission_id)
    except Exception as e:
        logger.error(f"Error in async evaluation wrapper: {e}")
        return {
            "success": False,
            "error": "wrapper_exception",
            "message": f"خطا در راه‌اندازی ارزیابی: {str(e)}",
            "submission_id": submission_id
        }


async def quick_evaluate_text_async(text: str, task_type: str) -> Dict[str, Any]:
    """
    Async wrapper for quick text evaluation.

    Args:
        text: Text to evaluate
        task_type: IELTS task type

    Returns:
        dict: Evaluation results
    """
    try:
        evaluator = get_ielts_evaluator()
        return await evaluator.quick_evaluate_text(text, task_type)
    except Exception as e:
        logger.error(f"Error in async quick evaluation wrapper: {e}")
        return {
            "success": False,
            "error": "wrapper_exception",
            "message": f"خطا در ارزیابی سریع: {str(e)}"
        }