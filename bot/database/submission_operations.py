"""
Database operations for submission management.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from shared.database import get_db_session
from shared.models.submission import Submission
from shared.models.user import User
from shared.models.system_log import SystemLog
from shared.constants import TaskType, SubmissionStatus

logger = logging.getLogger(__name__)


class SubmissionOperations:
    """
    Database operations class for submission management.
    """

    @staticmethod
    def create_submission(user_id: int, submission_text: str, task_type: TaskType,
                          word_count: int) -> Optional[Submission]:
        """
        Create a new submission.

        Args:
            user_id: User database ID
            submission_text: Text content of submission
            task_type: IELTS task type (Task 1 or Task 2)
            word_count: Number of words in submission

        Returns:
            Submission object if successful, None otherwise
        """
        try:
            with get_db_session() as session:
                submission = Submission(
                    user_id=user_id,
                    submission_text=submission_text,
                    task_type=task_type,
                    word_count=word_count,
                    submission_date=datetime.utcnow(),
                    status=SubmissionStatus.PENDING
                )

                session.add(submission)
                session.flush()  # Get the ID

                # Log submission creation
                user = session.query(User).filter_by(id=user_id).first()
                telegram_id = user.telegram_id if user else None

                log_entry = SystemLog.create_log(
                    level="INFO",
                    message=f"Submission created: {task_type.value}, {word_count} words",
                    module="submission_operations",
                    user_id=user_id,
                    telegram_id=telegram_id
                )
                session.add(log_entry)

                logger.info(f"Submission created: ID={submission.id}, User={user_id}")
                return submission

        except Exception as e:
            logger.error(f"Error creating submission for user {user_id}: {e}")
            return None

    @staticmethod
    def get_submission_by_id(submission_id: int) -> Optional[Submission]:
        """
        Get submission by ID.

        Args:
            submission_id: Submission database ID

        Returns:
            Submission object if found, None otherwise
        """
        try:
            with get_db_session() as session:
                submission = session.query(Submission).filter_by(id=submission_id).first()
                if submission:
                    session.expunge(submission)
                return submission
        except Exception as e:
            logger.error(f"Error getting submission {submission_id}: {e}")
            return None

    @staticmethod
    def update_submission_scores(submission_id: int, task_achievement: float,
                                 coherence_cohesion: float, lexical_resource: float,
                                 grammatical_accuracy: float) -> bool:
        """
        Update submission scores.

        Args:
            submission_id: Submission database ID
            task_achievement: Task Achievement score (0-9)
            coherence_cohesion: Coherence & Cohesion score (0-9)
            lexical_resource: Lexical Resource score (0-9)
            grammatical_accuracy: Grammatical Range & Accuracy score (0-9)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                submission = session.query(Submission).filter_by(id=submission_id).first()
                if submission:
                    submission.set_scores(
                        task_achievement=task_achievement,
                        coherence_cohesion=coherence_cohesion,
                        lexical_resource=lexical_resource,
                        grammatical_accuracy=grammatical_accuracy
                    )

                    # Log score update
                    log_entry = SystemLog.create_log(
                        level="INFO",
                        message=f"Submission scores updated: overall={submission.overall_score}",
                        module="submission_operations",
                        user_id=submission.user_id
                    )
                    session.add(log_entry)

                    logger.info(f"Scores updated for submission {submission_id}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating scores for submission {submission_id}: {e}")
            return False

    @staticmethod
    def complete_submission(submission_id: int, feedback_text: str = None,
                            processing_time: int = None) -> bool:
        """
        Mark submission as completed.

        Args:
            submission_id: Submission database ID
            feedback_text: AI feedback text (optional)
            processing_time: Processing time in seconds (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                submission = session.query(Submission).filter_by(id=submission_id).first()
                if submission:
                    submission.mark_completed(feedback_text, processing_time)

                    # Log completion
                    log_entry = SystemLog.create_log(
                        level="INFO",
                        message=f"Submission completed: processing_time={processing_time}s",
                        module="submission_operations",
                        user_id=submission.user_id
                    )
                    session.add(log_entry)

                    logger.info(f"Submission {submission_id} marked as completed")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error completing submission {submission_id}: {e}")
            return False

    @staticmethod
    def fail_submission(submission_id: int, error_message: str = None) -> bool:
        """
        Mark submission as failed.

        Args:
            submission_id: Submission database ID
            error_message: Error message (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with get_db_session() as session:
                submission = session.query(Submission).filter_by(id=submission_id).first()
                if submission:
                    submission.mark_failed(error_message)

                    # Log failure
                    log_entry = SystemLog.create_log(
                        level="ERROR",
                        message=f"Submission failed: {error_message or 'Unknown error'}",
                        module="submission_operations",
                        user_id=submission.user_id
                    )
                    session.add(log_entry)

                    logger.error(f"Submission {submission_id} marked as failed")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error failing submission {submission_id}: {e}")
            return False

    @staticmethod
    def get_user_submissions(user_id: int, limit: int = 10,
                             status: SubmissionStatus = None) -> List[Submission]:
        """
        Get user's submissions.

        Args:
            user_id: User database ID
            limit: Maximum number of submissions to return
            status: Filter by status (optional)

        Returns:
            List of Submission objects
        """
        try:
            with get_db_session() as session:
                query = session.query(Submission).filter_by(user_id=user_id)

                if status:
                    query = query.filter_by(status=status)

                submissions = (
                    query.order_by(Submission.submission_date.desc())
                    .limit(limit)
                    .all()
                )

                # Detach from session
                for submission in submissions:
                    session.expunge(submission)

                return submissions
        except Exception as e:
            logger.error(f"Error getting submissions for user {user_id}: {e}")
            return []

    @staticmethod
    def get_pending_submissions(limit: int = 50) -> List[Submission]:
        """
        Get pending submissions for processing.

        Args:
            limit: Maximum number of submissions to return

        Returns:
            List of pending Submission objects
        """
        try:
            with get_db_session() as session:
                submissions = (
                    session.query(Submission)
                    .filter_by(status=SubmissionStatus.PENDING)
                    .order_by(Submission.submission_date.asc())
                    .limit(limit)
                    .all()
                )

                # Detach from session
                for submission in submissions:
                    session.expunge(submission)

                return submissions
        except Exception as e:
            logger.error(f"Error getting pending submissions: {e}")
            return []

    @staticmethod
    def get_submission_statistics() -> Dict[str, Any]:
        """
        Get submission statistics.

        Returns:
            dict: Various submission statistics
        """
        try:
            with get_db_session() as session:
                total_submissions = session.query(Submission).count()

                completed_submissions = session.query(Submission).filter_by(
                    status=SubmissionStatus.COMPLETED
                ).count()

                pending_submissions = session.query(Submission).filter_by(
                    status=SubmissionStatus.PENDING
                ).count()

                failed_submissions = session.query(Submission).filter_by(
                    status=SubmissionStatus.FAILED
                ).count()

                # Task type distribution
                task1_count = session.query(Submission).filter_by(
                    task_type=TaskType.TASK1
                ).count()

                task2_count = session.query(Submission).filter_by(
                    task_type=TaskType.TASK2
                ).count()

                # Average scores (only completed submissions)
                from sqlalchemy import func

                avg_scores = session.query(
                    func.avg(Submission.overall_score).label('avg_overall'),
                    func.avg(Submission.task_achievement_score).label('avg_task_achievement'),
                    func.avg(Submission.coherence_cohesion_score).label('avg_coherence'),
                    func.avg(Submission.lexical_resource_score).label('avg_lexical'),
                    func.avg(Submission.grammatical_accuracy_score).label('avg_grammar')
                ).filter_by(status=SubmissionStatus.COMPLETED).first()

                return {
                    'total_submissions': total_submissions,
                    'completed_submissions': completed_submissions,
                    'pending_submissions': pending_submissions,
                    'failed_submissions': failed_submissions,
                    'task1_count': task1_count,
                    'task2_count': task2_count,
                    'completion_rate': (
                                completed_submissions / total_submissions * 100) if total_submissions > 0 else 0,
                    'average_scores': {
                        'overall': float(avg_scores.avg_overall or 0),
                        'task_achievement': float(avg_scores.avg_task_achievement or 0),
                        'coherence_cohesion': float(avg_scores.avg_coherence or 0),
                        'lexical_resource': float(avg_scores.avg_lexical or 0),
                        'grammatical_accuracy': float(avg_scores.avg_grammar or 0)
                    }
                }
        except Exception as e:
            logger.error(f"Error getting submission statistics: {e}")
            return {
                'total_submissions': 0,
                'completed_submissions': 0,
                'pending_submissions': 0,
                'failed_submissions': 0,
                'task1_count': 0,
                'task2_count': 0,
                'completion_rate': 0,
                'average_scores': {
                    'overall': 0,
                    'task_achievement': 0,
                    'coherence_cohesion': 0,
                    'lexical_resource': 0,
                    'grammatical_accuracy': 0
                }
            }