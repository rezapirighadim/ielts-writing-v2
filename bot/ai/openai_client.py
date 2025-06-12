"""
OpenAI API client for IELTS writing evaluation.
"""

import logging
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from openai import OpenAI
from openai.types.chat import ChatCompletion  # Add this import back
import os
from shared.config import config

logger = logging.getLogger(__name__)


@dataclass
class AIEvaluationResult:
    """
    Data class for AI evaluation results.

    Python Concept: Dataclasses provide a clean structure for
    complex evaluation data with automatic serialization support.
    """
    success: bool
    task_achievement_score: Optional[float] = None
    coherence_cohesion_score: Optional[float] = None
    lexical_resource_score: Optional[float] = None
    grammatical_accuracy_score: Optional[float] = None
    overall_score: Optional[float] = None

    # Detailed feedback
    feedback_text: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    improvement_suggestions: Optional[List[str]] = None

    # Processing metadata
    processing_time_seconds: Optional[int] = None
    model_version: Optional[str] = None
    tokens_used: Optional[int] = None
    error_message: Optional[str] = None

    # Raw response for debugging
    raw_response: Optional[str] = None


class OpenAIClient:
    """
    OpenAI API client for IELTS writing evaluation.

    Python Concept: This class encapsulates all OpenAI API interactions
    and provides a clean interface for IELTS-specific evaluations.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (if None, reads from config)
            model: OpenAI model to use for evaluation (if None, reads from config)
        """
        self.api_key = api_key or config.OPENAI_API_KEY
        self.model = model or config.OPENAI_MODEL
        self.client = None
        self.max_retries = config.OPENAI_MAX_RETRIES
        self.retry_delay = config.OPENAI_RETRY_DELAY
        self.timeout = config.OPENAI_TIMEOUT

        if not self.api_key:
            logger.error("OpenAI API key not provided")
            raise ValueError("OpenAI API key is required")

        try:
            # Initialize OpenAI client with minimal parameters for compatibility
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"✅ OpenAI client initialized with model: {self.model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Test OpenAI API connection.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Test connection. Reply with 'OK'."}
                ],
                max_tokens=10,
                temperature=0
            )

            if response.choices and response.choices[0].message.content:
                logger.info("✅ OpenAI API connection test successful")
                return True

            logger.error("❌ OpenAI API connection test failed - no response")
            return False

        except Exception as e:
            logger.error(f"❌ OpenAI API connection test failed: {e}")
            return False

    async def evaluate_ielts_writing(self, text: str, task_type: str,
                                   additional_context: Optional[Dict[str, Any]] = None) -> AIEvaluationResult:
        """
        Evaluate IELTS writing using OpenAI API.

        Args:
            text: The text to evaluate
            task_type: IELTS task type ('task1' or 'task2')
            additional_context: Additional context like word count, analysis data

        Returns:
            AIEvaluationResult: Comprehensive evaluation result
        """
        start_time = time.time()

        try:
            # Build evaluation prompt
            prompt = self._build_evaluation_prompt(text, task_type, additional_context)

            # Make API call with retries
            response = await self._make_api_call_with_retries(prompt)

            if not response:
                return AIEvaluationResult(
                    success=False,
                    error_message="Failed to get response from OpenAI API",
                    processing_time_seconds=int(time.time() - start_time)
                )

            # Parse response
            evaluation = self._parse_evaluation_response(response)

            # Add metadata
            evaluation.processing_time_seconds = int(time.time() - start_time)
            evaluation.model_version = self.model
            evaluation.tokens_used = response.usage.total_tokens if response.usage else None

            logger.info(f"✅ IELTS evaluation completed in {evaluation.processing_time_seconds}s")
            return evaluation

        except Exception as e:
            logger.error(f"❌ Error in IELTS evaluation: {e}")
            return AIEvaluationResult(
                success=False,
                error_message=str(e),
                processing_time_seconds=int(time.time() - start_time)
            )

    def _build_evaluation_prompt(self, text: str, task_type: str,
                               additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Build comprehensive evaluation prompt for IELTS writing.

        Args:
            text: Text to evaluate
            task_type: Task type ('task1' or 'task2')
            additional_context: Additional context data

        Returns:
            str: Complete evaluation prompt
        """
        # Get task-specific requirements
        task_requirements = self._get_task_requirements(task_type)

        # Build context information
        context_info = ""
        if additional_context:
            word_count = additional_context.get('word_count', 'Unknown')
            readability = additional_context.get('readability_score', 'Unknown')
            context_info = f"""
Additional Context:
- Word Count: {word_count}
- Readability Score: {readability}
- Analysis Method: Enhanced validation
"""

        # Build comprehensive prompt
        prompt = f"""You are an expert IELTS examiner evaluating a {task_type.upper()} writing sample. 

{task_requirements}

{context_info}

WRITING SAMPLE TO EVALUATE:
"{text}"

Please provide a comprehensive evaluation following this EXACT JSON format:

{{
    "task_achievement_score": 7.5,
    "coherence_cohesion_score": 7.0,
    "lexical_resource_score": 6.5,
    "grammatical_accuracy_score": 7.0,
    "overall_score": 7.0,
    "feedback_text": "Overall assessment in Persian...",
    "strengths": [
        "Strength 1 in Persian",
        "Strength 2 in Persian"
    ],
    "weaknesses": [
        "Weakness 1 in Persian", 
        "Weakness 2 in Persian"
    ],
    "improvement_suggestions": [
        "Suggestion 1 in Persian",
        "Suggestion 2 in Persian"
    ]
}}

CRITICAL REQUIREMENTS:
1. Scores must be decimal numbers between 0.0 and 9.0 (IELTS scale)
2. Overall score should be the average of the four band scores
3. All text feedback must be in Persian (Farsi)
4. Be specific and constructive in feedback
5. Follow IELTS official band descriptors strictly
6. Respond with ONLY the JSON - no additional text

Evaluate now:"""

        return prompt

    def _get_task_requirements(self, task_type: str) -> str:
        """Get task-specific requirements and assessment criteria."""

        if task_type == 'task1':
            return """
IELTS ACADEMIC WRITING TASK 1 EVALUATION:

Task Requirements:
- Minimum 150 words
- Describe visual information (graphs, charts, tables, diagrams)
- Present key features and make comparisons
- Write in formal academic style
- Complete task in 20 minutes

Assessment Criteria:
1. TASK ACHIEVEMENT (25%):
   - Addresses all requirements of the task
   - Presents clear overview of main trends/differences/stages
   - Highlights key features with relevant data
   - May not require personal opinion

2. COHERENCE AND COHESION (25%):
   - Logical organization of information
   - Clear progression throughout
   - Appropriate use of cohesive devices
   - Paragraphs are well-linked

3. LEXICAL RESOURCE (25%):
   - Range of vocabulary appropriate for the task
   - Accuracy in word choice and formation
   - Ability to paraphrase effectively
   - Less repetition of words/phrases

4. GRAMMATICAL RANGE AND ACCURACY (25%):
   - Range of grammatical structures
   - Accuracy in grammar and punctuation
   - Error-free sentences show good control
   - Complex structures attempted
"""
        else:  # task2
            return """
IELTS ACADEMIC WRITING TASK 2 EVALUATION:

Task Requirements:
- Minimum 250 words
- Present argument or discuss topic
- Support ideas with examples and evidence
- Write in formal academic style
- Complete task in 40 minutes

Assessment Criteria:
1. TASK ACHIEVEMENT (25%):
   - Addresses all parts of the task
   - Presents clear position throughout
   - Develops ideas with relevant support
   - Stays on topic throughout

2. COHERENCE AND COHESION (25%):
   - Logical organization and sequencing
   - Clear central topic in each paragraph
   - Appropriate use of linking devices
   - Effective paragraphing

3. LEXICAL RESOURCE (25%):
   - Wide range of vocabulary
   - Natural and appropriate usage
   - Awareness of style and collocation
   - Rare errors that don't impede communication

4. GRAMMATICAL RANGE AND ACCURACY (25%):
   - Wide range of grammatical structures
   - Flexible and accurate usage
   - Error-free sentences are frequent
   - Minor errors don't reduce communication
"""

    async def _make_api_call_with_retries(self, prompt: str) -> Optional[ChatCompletion]:
        """
        Make API call with retry logic.

        Args:
            prompt: Evaluation prompt

        Returns:
            ChatCompletion response or None if failed
        """
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert IELTS examiner. Respond with valid JSON only."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.3,  # Consistent but not too rigid
                    response_format={"type": "json_object"}  # Ensure JSON response
                )

                return response

            except Exception as e:
                logger.warning(f"API call attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {self.max_retries} API call attempts failed")

        return None

    def _parse_evaluation_response(self, response: ChatCompletion) -> AIEvaluationResult:
        """
        Parse OpenAI response into evaluation result.

        Args:
            response: OpenAI ChatCompletion response

        Returns:
            AIEvaluationResult: Parsed evaluation data
        """
        try:
            if not response.choices or not response.choices[0].message.content:
                return AIEvaluationResult(
                    success=False,
                    error_message="Empty response from OpenAI"
                )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                return AIEvaluationResult(
                    success=False,
                    error_message=f"Invalid JSON response: {str(e)}",
                    raw_response=content
                )

            # Validate and extract scores
            required_scores = [
                'task_achievement_score',
                'coherence_cohesion_score',
                'lexical_resource_score',
                'grammatical_accuracy_score'
            ]

            for score_key in required_scores:
                if score_key not in data:
                    return AIEvaluationResult(
                        success=False,
                        error_message=f"Missing required score: {score_key}",
                        raw_response=content
                    )

            # Calculate overall score if not provided
            if 'overall_score' not in data:
                scores = [data[key] for key in required_scores]
                data['overall_score'] = round(sum(scores) / len(scores), 1)

            # Create result
            return AIEvaluationResult(
                success=True,
                task_achievement_score=float(data['task_achievement_score']),
                coherence_cohesion_score=float(data['coherence_cohesion_score']),
                lexical_resource_score=float(data['lexical_resource_score']),
                grammatical_accuracy_score=float(data['grammatical_accuracy_score']),
                overall_score=float(data['overall_score']),
                feedback_text=data.get('feedback_text', ''),
                strengths=data.get('strengths', []),
                weaknesses=data.get('weaknesses', []),
                improvement_suggestions=data.get('improvement_suggestions', []),
                raw_response=content
            )

        except Exception as e:
            logger.error(f"Error parsing evaluation response: {e}")
            return AIEvaluationResult(
                success=False,
                error_message=f"Response parsing error: {str(e)}",
                raw_response=response.choices[0].message.content if response.choices else None
            )

    def get_api_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics (placeholder - would need tracking implementation).

        Returns:
            dict: Usage statistics
        """
        # In a production system, you'd track these metrics
        return {
            "model": self.model,
            "api_key_status": "configured" if self.api_key else "missing",
            "client_status": "initialized" if self.client else "not_initialized",
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay
        }


# Global OpenAI client instance (initialized when needed)
_openai_client: Optional[OpenAIClient] = None


def get_openai_client() -> OpenAIClient:
    """
    Get or create global OpenAI client instance.

    Returns:
        OpenAIClient: Configured OpenAI client

    Raises:
        ValueError: If API key is not configured
    """
    global _openai_client

    if _openai_client is None:
        _openai_client = OpenAIClient()

    return _openai_client


def test_openai_integration() -> bool:
    """
    Test OpenAI integration.

    Returns:
        bool: True if integration is working, False otherwise
    """
    try:
        client = get_openai_client()
        return client.test_connection()
    except Exception as e:
        logger.error(f"OpenAI integration test failed: {e}")
        return False