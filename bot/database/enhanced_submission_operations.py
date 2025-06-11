"""
Enhanced submission database operations with detailed analysis storage.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, or_, desc, func
from shared.database import get_db_session
from shared.models.submission import Submission
from shared.models.user import User
from database.user_operations import UserOperations

logger = logging.getLogger(__name__)


class EnhancedSubmissionOperations:
    """
    Enhanced submission operations with detailed analysis and validation data storage.

    Python Concept: This class extends basic submission operations with
    comprehensive data storage for word count analysis, text analysis,
    and validation results.
    """

    @staticmethod
    def create_enhanced_submission(submission_data: Dict[str, Any]) -> Optional[int]:
        """
        Create a new submission with enhanced validation and analysis data.

        Args:
            submission_data: Comprehensive submission data including analysis results

        Returns:
            int: Submission ID if successful, None otherwise
        """
        try:
            with get_db_session() as session:
                # Create submission object with enhanced data
                submission = Submission(
                    user_id=submission_data['user_id'],
                    submission_text=submission_data['submission_text'],
                    task_type=submission_data['task_type'],
                    word_count=submission_data['word_count'],
                    character_count=submission_data.get('character_count', len(submission_data['submission_text'])),
                    submission_date=submission_data.get('submission_date', datetime.utcnow()),
                    status='pending'
                )

                # Store enhanced validation data as JSON
                validation_data = {
                    'word_count_analysis': submission_data.get('word_count_analysis', {}),
                    'text_analysis': submission_data.get('text_analysis', {}),
                    'language_analysis': submission_data.get('language_analysis', {}),
                    'quality_analysis': submission_data.get('quality_analysis', {}),
                    'validation_method': submission_data.get('validation_method', 'enhanced'),
                    'confidence_score': submission_data.get('confidence_score', 0.0)
                }

                # Convert complex objects to serializable format
                validation_json = EnhancedSubmissionOperations._serialize_validation_data(validation_data)
                submission.validation_data = json.dumps(validation_json, ensure_ascii=False)

                # Store analysis metadata
                analysis_metadata = {
                    'readability_score': submission_data.get('readability_score', 0.0),
                    'overall_quality': submission_data.get('overall_quality', 'unknown'),
                    'sentence_count': submission_data.get('sentence_count', 0),
                    'paragraph_count': submission_data.get('paragraph_count', 0),
                    'lexical_diversity': submission_data.get('lexical_diversity', 0.0),
                    'academic_words_count': submission_data.get('academic_words_count', 0),
                    'complexity_score': submission_data.get('complexity_score', 0.0),
                    'structure_score': submission_data.get('structure_score', 0.0),
                    'recommendations_count': submission_data.get('recommendations_count', 0)
                }

                submission.analysis_metadata = json.dumps(analysis_metadata, ensure_ascii=False)

                # Add to session and commit
                session.add(submission)
                session.flush()  # Get the ID
                submission_id = submission.id

                # Update user submission count - need to get telegram_id for UserOperations
                user = session.query(User).filter_by(id=submission_data['user_id']).first()
                if user:
                    UserOperations.increment_user_submissions(user.telegram_id)

                session.commit()

                logger.info(f"Enhanced submission {submission_id} created for user {submission_data['user_id']}")
                return submission_id

        except IntegrityError as e:
            logger.error(f"Integrity error creating enhanced submission: {e}")
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error creating enhanced submission: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating enhanced submission: {e}")
            return None

    @staticmethod
    def _serialize_validation_data(validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize complex validation data objects for JSON storage.

        Args:
            validation_data: Raw validation data with complex objects

        Returns:
            dict: Serialized data safe for JSON storage
        """
        try:
            serialized = {}

            for key, value in validation_data.items():
                if hasattr(value, '__dict__'):
                    # Convert dataclass or object to dict
                    if hasattr(value, '_asdict'):
                        serialized[key] = value._asdict()
                    else:
                        serialized[key] = value.__dict__
                elif isinstance(value, (list, tuple)):
                    # Handle lists/tuples of objects
                    serialized[key] = [
                        item.__dict__ if hasattr(item, '__dict__') else item
                        for item in value
                    ]
                else:
                    # Simple types that can be JSON serialized
                    serialized[key] = value

            return serialized

        except Exception as e:
            logger.error(f"Error serializing validation data: {e}")
            return {}

    @staticmethod
    def update_submission_analysis(submission_id: int, analysis_data: Dict[str, Any]) -> bool:
        """
        Update submission with AI analysis results.

        Args:
            submission_id: Submission ID to update
            analysis_data: AI analysis results

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                submission = session.query(Submission).filter_by(id=submission_id).first()

                if not submission:
                    logger.error(f"Submission {submission_id} not found for analysis update")
                    return False

                # Update IELTS scores
                submission.task_achievement_score = analysis_data.get('task_achievement_score')
                submission.coherence_cohesion_score = analysis_data.get('coherence_cohesion_score')
                submission.lexical_resource_score = analysis_data.get('lexical_resource_score')
                submission.grammatical_accuracy_score = analysis_data.get('grammatical_accuracy_score')
                submission.overall_score = analysis_data.get('overall_score')

                # Update feedback and processing info
                submission.feedback_text = analysis_data.get('feedback_text')
                submission.processing_time_seconds = analysis_data.get('processing_time_seconds')
                submission.status = analysis_data.get('status', 'completed')

                # Store detailed AI analysis data
                ai_analysis = {
                    'ai_model_version': analysis_data.get('ai_model_version', 'unknown'),
                    'analysis_timestamp': datetime.utcnow().isoformat(),
                    'detailed_feedback': analysis_data.get('detailed_feedback', {}),
                    'scoring_breakdown': analysis_data.get('scoring_breakdown', {}),
                    'improvement_suggestions': analysis_data.get('improvement_suggestions', []),
                    'strengths': analysis_data.get('strengths', []),
                    'weaknesses': analysis_data.get('weaknesses', [])
                }

                submission.ai_analysis_data = json.dumps(ai_analysis, ensure_ascii=False)

                session.commit()

                logger.info(f"Enhanced analysis updated for submission {submission_id}")
                return True

        except SQLAlchemyError as e:
            logger.error(f"Database error updating submission analysis: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating submission analysis: {e}")
            return False

    @staticmethod
    def get_submission_with_analysis(submission_id: int) -> Optional[Dict[str, Any]]:
        """
        Get submission with all analysis data.

        Args:
            submission_id: Submission ID

        Returns:
            dict: Complete submission data with analysis, None if not found
        """
        try:
            with get_db_session() as session:
                submission = session.query(Submission).filter_by(id=submission_id).first()

                if not submission:
                    return None

                # Parse stored JSON data
                validation_data = {}
                analysis_metadata = {}
                ai_analysis_data = {}

                try:
                    if submission.validation_data:
                        validation_data = json.loads(submission.validation_data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid validation_data JSON for submission {submission_id}")

                try:
                    if submission.analysis_metadata:
                        analysis_metadata = json.loads(submission.analysis_metadata)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid analysis_metadata JSON for submission {submission_id}")

                try:
                    if submission.ai_analysis_data:
                        ai_analysis_data = json.loads(submission.ai_analysis_data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid ai_analysis_data JSON for submission {submission_id}")

                return {
                    'id': submission.id,
                    'user_id': submission.user_id,
                    'submission_text': submission.submission_text,
                    'task_type': submission.task_type,
                    'word_count': submission.word_count,
                    'character_count': submission.character_count,
                    'submission_date': submission.submission_date,
                    'status': submission.status,

                    # IELTS scores
                    'task_achievement_score': submission.task_achievement_score,
                    'coherence_cohesion_score': submission.coherence_cohesion_score,
                    'lexical_resource_score': submission.lexical_resource_score,
                    'grammatical_accuracy_score': submission.grammatical_accuracy_score,
                    'overall_score': submission.overall_score,

                    # Feedback and processing
                    'feedback_text': submission.feedback_text,
                    'processing_time_seconds': submission.processing_time_seconds,

                    # Enhanced analysis data
                    'validation_data': validation_data,
                    'analysis_metadata': analysis_metadata,
                    'ai_analysis_data': ai_analysis_data
                }

        except SQLAlchemyError as e:
            logger.error(f"Database error getting submission with analysis: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting submission with analysis: {e}")
            return None

    @staticmethod
    def get_user_submissions_with_stats(user_id: int, limit: int = 10,
                                       include_analysis: bool = True) -> List[Dict[str, Any]]:
        """
        Get user submissions with analysis statistics.

        Args:
            user_id: User ID
            limit: Maximum number of submissions to return
            include_analysis: Whether to include detailed analysis data

        Returns:
            List of submission dictionaries with analysis data
        """
        try:
            with get_db_session() as session:
                query = (
                    session.query(Submission)
                    .filter(Submission.user_id == user_id)
                    .order_by(desc(Submission.submission_date))
                    .limit(limit)
                )

                submissions = query.all()
                result = []

                for submission in submissions:
                    submission_dict = {
                        'id': submission.id,
                        'task_type': submission.task_type,
                        'word_count': submission.word_count,
                        'submission_date': submission.submission_date,
                        'status': submission.status,
                        'overall_score': submission.overall_score,
                        'processing_time_seconds': submission.processing_time_seconds
                    }

                    if include_analysis:
                        # Add parsed analysis metadata for quick stats
                        try:
                            if submission.analysis_metadata:
                                metadata = json.loads(submission.analysis_metadata)
                                submission_dict.update({
                                    'readability_score': metadata.get('readability_score', 0),
                                    'overall_quality': metadata.get('overall_quality', 'unknown'),
                                    'lexical_diversity': metadata.get('lexical_diversity', 0),
                                    'complexity_score': metadata.get('complexity_score', 0),
                                    'structure_score': metadata.get('structure_score', 0)
                                })
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid analysis metadata for submission {submission.id}")

                    result.append(submission_dict)

                return result

        except SQLAlchemyError as e:
            logger.error(f"Database error getting user submissions with stats: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting user submissions with stats: {e}")
            return []

    @staticmethod
    def get_submission_analytics(user_id: Optional[int] = None,
                               task_type: Optional[str] = None,
                               days_back: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive submission analytics.

        Args:
            user_id: Specific user ID (None for all users)
            task_type: Specific task type (None for all types)
            days_back: Number of days to analyze

        Returns:
            dict: Analytics data
        """
        try:
            with get_db_session() as session:
                # Base query
                query = session.query(Submission)

                # Apply filters
                if user_id:
                    query = query.filter(Submission.user_id == user_id)
                if task_type:
                    query = query.filter(Submission.task_type == task_type)

                # Date filter
                cutoff_date = datetime.utcnow() - timedelta(days=days_back)
                query = query.filter(Submission.submission_date >= cutoff_date)

                submissions = query.all()

                if not submissions:
                    return {
                        'total_submissions': 0,
                        'average_scores': {},
                        'word_count_stats': {},
                        'quality_distribution': {},
                        'task_type_breakdown': {}
                    }

                # Calculate statistics
                total_submissions = len(submissions)
                completed_submissions = [s for s in submissions if s.status == 'completed']

                # Score statistics
                scores = {
                    'task_achievement': [s.task_achievement_score for s in completed_submissions if s.task_achievement_score],
                    'coherence_cohesion': [s.coherence_cohesion_score for s in completed_submissions if s.coherence_cohesion_score],
                    'lexical_resource': [s.lexical_resource_score for s in completed_submissions if s.lexical_resource_score],
                    'grammatical_accuracy': [s.grammatical_accuracy_score for s in completed_submissions if s.grammatical_accuracy_score],
                    'overall': [s.overall_score for s in completed_submissions if s.overall_score]
                }

                average_scores = {}
                for score_type, score_list in scores.items():
                    if score_list:
                        average_scores[score_type] = {
                            'average': round(sum(score_list) / len(score_list), 1),
                            'min': min(score_list),
                            'max': max(score_list),
                            'count': len(score_list)
                        }

                # Word count statistics
                word_counts = [s.word_count for s in submissions if s.word_count]
                word_count_stats = {}
                if word_counts:
                    word_count_stats = {
                        'average': round(sum(word_counts) / len(word_counts)),
                        'min': min(word_counts),
                        'max': max(word_counts),
                        'median': sorted(word_counts)[len(word_counts) // 2]
                    }

                # Quality distribution
                quality_counts = {}
                for submission in submissions:
                    if submission.analysis_metadata:
                        try:
                            metadata = json.loads(submission.analysis_metadata)
                            quality = metadata.get('overall_quality', 'unknown')
                            quality_counts[quality] = quality_counts.get(quality, 0) + 1
                        except json.JSONDecodeError:
                            quality_counts['unknown'] = quality_counts.get('unknown', 0) + 1

                # Task type breakdown
                task_type_counts = {}
                for submission in submissions:
                    task = submission.task_type
                    task_type_counts[task] = task_type_counts.get(task, 0) + 1

                return {
                    'total_submissions': total_submissions,
                    'completed_submissions': len(completed_submissions),
                    'average_scores': average_scores,
                    'word_count_stats': word_count_stats,
                    'quality_distribution': quality_counts,
                    'task_type_breakdown': task_type_counts,
                    'analysis_period_days': days_back
                }

        except SQLAlchemyError as e:
            logger.error(f"Database error getting submission analytics: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting submission analytics: {e}")
            return {}

    @staticmethod
    def delete_submission(submission_id: int, user_id: int) -> bool:
        """
        Delete a submission (with user verification).

        Args:
            submission_id: Submission ID to delete
            user_id: User ID for verification

        Returns:
            bool: True if successfully deleted, False otherwise
        """
        try:
            with get_db_session() as session:
                submission = session.query(Submission).filter_by(
                    id=submission_id,
                    user_id=user_id
                ).first()

                if not submission:
                    logger.warning(f"Submission {submission_id} not found for user {user_id}")
                    return False

                session.delete(submission)
                session.commit()

                logger.info(f"Submission {submission_id} deleted by user {user_id}")
                return True

        except SQLAlchemyError as e:
            logger.error(f"Database error deleting submission: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting submission: {e}")
            return False

    @staticmethod
    def search_submissions(user_id: Optional[int] = None,
                          search_text: Optional[str] = None,
                          min_score: Optional[float] = None,
                          max_score: Optional[float] = None,
                          task_type: Optional[str] = None,
                          status: Optional[str] = None,
                          limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search submissions with various filters.

        Args:
            user_id: Filter by user ID
            search_text: Search in submission text
            min_score: Minimum overall score
            max_score: Maximum overall score
            task_type: Filter by task type
            status: Filter by status
            limit: Maximum results

        Returns:
            List of matching submissions
        """
        try:
            with get_db_session() as session:
                query = session.query(Submission)

                # Apply filters
                if user_id:
                    query = query.filter(Submission.user_id == user_id)

                if search_text:
                    query = query.filter(Submission.submission_text.contains(search_text))

                if min_score is not None:
                    query = query.filter(Submission.overall_score >= min_score)

                if max_score is not None:
                    query = query.filter(Submission.overall_score <= max_score)

                if task_type:
                    query = query.filter(Submission.task_type == task_type)

                if status:
                    query = query.filter(Submission.status == status)

                # Order and limit
                query = query.order_by(desc(Submission.submission_date)).limit(limit)

                submissions = query.all()

                return [
                    {
                        'id': s.id,
                        'user_id': s.user_id,
                        'task_type': s.task_type,
                        'word_count': s.word_count,
                        'overall_score': s.overall_score,
                        'submission_date': s.submission_date,
                        'status': s.status,
                        'text_preview': s.submission_text[:100] + '...' if len(s.submission_text) > 100 else s.submission_text
                    }
                    for s in submissions
                ]

        except SQLAlchemyError as e:
            logger.error(f"Database error searching submissions: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching submissions: {e}")
            return []