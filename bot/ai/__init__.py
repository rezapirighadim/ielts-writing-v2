"""
AI module for IELTS writing evaluation.
"""

# Make key classes and functions easily importable
from .openai_client import OpenAIClient, get_openai_client, test_openai_integration, AIEvaluationResult
from .ielts_evaluator import IELTSEvaluator, get_ielts_evaluator, evaluate_submission_async, quick_evaluate_text_async

__all__ = [
    'OpenAIClient',
    'get_openai_client',
    'test_openai_integration',
    'AIEvaluationResult',
    'IELTSEvaluator',
    'get_ielts_evaluator',
    'evaluate_submission_async',
    'quick_evaluate_text_async'
]