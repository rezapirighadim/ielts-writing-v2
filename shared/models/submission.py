"""
Submission model for storing IELTS writing submissions and evaluations.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import relationship
from ..database import Base
from ..constants import TaskType, SubmissionStatus


class Submission(Base):
    """
    Submission model representing user writing submissions and AI evaluations.
    """

    __tablename__ = 'submissions'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to user
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Submission content
    submission_text = Column(Text, nullable=False)
    task_type = Column(SQLEnum(TaskType), nullable=False)
    word_count = Column(Integer, nullable=False)
    submission_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # IELTS scoring (0.0 to 9.0 with 0.5 increments)
    # Python Concept: DECIMAL is used for precise decimal numbers
    # DECIMAL(3,1) means 3 total digits with 1 decimal place (e.g., 9.5)
    task_achievement_score = Column(DECIMAL(3, 1), nullable=True)
    coherence_cohesion_score = Column(DECIMAL(3, 1), nullable=True)
    lexical_resource_score = Column(DECIMAL(3, 1), nullable=True)
    grammatical_accuracy_score = Column(DECIMAL(3, 1), nullable=True)
    overall_score = Column(DECIMAL(3, 1), nullable=True)

    # AI feedback
    feedback_text = Column(Text, nullable=True)

    # Processing information
    processing_time_seconds = Column(Integer, nullable=True)
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)

    # Relationships
    user = relationship("User", back_populates="submissions")

    def __repr__(self) -> str:
        return f"<Submission(id={self.id}, user_id={self.user_id}, task_type={self.task_type.value}, status={self.status.value})>"

    def __str__(self) -> str:
        return f"Submission {self.id} - {self.task_type.value} ({self.word_count} words)"

    @property
    def is_completed(self) -> bool:
        """Check if submission has been processed."""
        return self.status == SubmissionStatus.COMPLETED

    @property
    def is_pending(self) -> bool:
        """Check if submission is pending processing."""
        return self.status == SubmissionStatus.PENDING

    @property
    def is_failed(self) -> bool:
        """Check if submission processing failed."""
        return self.status == SubmissionStatus.FAILED

    @property
    def has_scores(self) -> bool:
        """Check if submission has all required scores."""
        required_scores = [
            self.task_achievement_score,
            self.coherence_cohesion_score,
            self.lexical_resource_score,
            self.grammatical_accuracy_score,
            self.overall_score
        ]
        return all(score is not None for score in required_scores)

    @property
    def average_score(self) -> float:
        """Calculate average of component scores."""
        scores = [
            float(self.task_achievement_score or 0),
            float(self.coherence_cohesion_score or 0),
            float(self.lexical_resource_score or 0),
            float(self.grammatical_accuracy_score or 0)
        ]

        valid_scores = [score for score in scores if score > 0]
        if valid_scores:
            return sum(valid_scores) / len(valid_scores)
        return 0.0

    def set_scores(self, task_achievement: float, coherence_cohesion: float,
                   lexical_resource: float, grammatical_accuracy: float):
        """
        Set all component scores and calculate overall score.

        Args:
            task_achievement: Task Achievement score (0-9)
            coherence_cohesion: Coherence & Cohesion score (0-9)
            lexical_resource: Lexical Resource score (0-9)
            grammatical_accuracy: Grammatical Range & Accuracy score (0-9)
        """
        self.task_achievement_score = round(task_achievement, 1)
        self.coherence_cohesion_score = round(coherence_cohesion, 1)
        self.lexical_resource_score = round(lexical_resource, 1)
        self.grammatical_accuracy_score = round(grammatical_accuracy, 1)

        # Calculate overall score as average, rounded to nearest 0.5
        average = self.average_score
        self.overall_score = round(average * 2) / 2  # Round to nearest 0.5

    def mark_completed(self, feedback_text: str = None, processing_time: int = None):
        """Mark submission as completed with optional feedback."""
        self.status = SubmissionStatus.COMPLETED
        if feedback_text:
            self.feedback_text = feedback_text
        if processing_time:
            self.processing_time_seconds = processing_time

    def mark_failed(self, error_message: str = None):
        """Mark submission as failed with optional error message."""
        self.status = SubmissionStatus.FAILED
        if error_message:
            self.feedback_text = f"خطا در پردازش: {error_message}"

    def get_score_summary(self) -> dict:
        """Get a summary of all scores."""
        return {
            'task_achievement': float(self.task_achievement_score) if self.task_achievement_score else None,
            'coherence_cohesion': float(self.coherence_cohesion_score) if self.coherence_cohesion_score else None,
            'lexical_resource': float(self.lexical_resource_score) if self.lexical_resource_score else None,
            'grammatical_accuracy': float(self.grammatical_accuracy_score) if self.grammatical_accuracy_score else None,
            'overall_score': float(self.overall_score) if self.overall_score else None,
            'average_score': self.average_score
        }

    def to_dict(self) -> dict:
        """Convert submission to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'submission_text': self.submission_text,
            'task_type': self.task_type.value,
            'word_count': self.word_count,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'status': self.status.value,
            'scores': self.get_score_summary(),
            'feedback_text': self.feedback_text,
            'processing_time_seconds': self.processing_time_seconds,
            'is_completed': self.is_completed,
            'has_scores': self.has_scores
        }