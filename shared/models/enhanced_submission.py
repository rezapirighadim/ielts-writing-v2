"""
Enhanced submission model with additional fields for detailed analysis storage.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Decimal, Enum, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class EnhancedSubmission(Base):
    """
    Enhanced submission model with comprehensive analysis data storage.

    Note: This extends the base Submission model with additional fields
    for storing detailed validation and analysis results.
    """

    __tablename__ = 'enhanced_submissions'

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key to users
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Basic submission data
    submission_text = Column(Text, nullable=False)
    task_type = Column(Enum('task1', 'task2'), nullable=False)
    word_count = Column(Integer, nullable=False)
    character_count = Column(Integer, nullable=True)
    submission_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # IELTS scoring (decimal precision for accurate scoring)
    task_achievement_score = Column(Decimal(3, 1), nullable=True)
    coherence_cohesion_score = Column(Decimal(3, 1), nullable=True)
    lexical_resource_score = Column(Decimal(3, 1), nullable=True)
    grammatical_accuracy_score = Column(Decimal(3, 1), nullable=True)
    overall_score = Column(Decimal(3, 1), nullable=True)

    # Feedback and processing
    feedback_text = Column(Text, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    status = Column(Enum('pending', 'processing', 'completed', 'failed', 'cancelled'),
                    default='pending', nullable=False)

    # Enhanced analysis data (JSON fields)
    validation_data = Column(Text, nullable=True)  # JSON: word count analysis, language detection
    analysis_metadata = Column(Text, nullable=True)  # JSON: readability, complexity, structure scores
    ai_analysis_data = Column(Text, nullable=True)  # JSON: detailed AI feedback and breakdown

    # Performance metrics
    readability_score = Column(Decimal(5, 2), nullable=True)
    lexical_diversity = Column(Decimal(5, 3), nullable=True)
    sentence_complexity_score = Column(Decimal(5, 3), nullable=True)
    structure_quality_score = Column(Decimal(5, 3), nullable=True)

    # Content analysis
    sentence_count = Column(Integer, nullable=True)
    paragraph_count = Column(Integer, nullable=True)
    academic_words_count = Column(Integer, nullable=True)
    transition_words_count = Column(Integer, nullable=True)

    # Quality indicators
    overall_quality = Column(Enum('excellent', 'good', 'fair', 'needs_improvement', 'poor'), nullable=True)
    recommendations_count = Column(Integer, default=0)

    # Processing metadata
    validation_method = Column(String(50), default='enhanced')
    confidence_score = Column(Decimal(5, 3), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="enhanced_submissions")

    def __repr__(self) -> str:
        return f"<EnhancedSubmission(id={self.id}, user_id={self.user_id}, task={self.task_type}, score={self.overall_score})>"

    def __str__(self) -> str:
        return f"Submission {self.id}: {self.task_type} - {self.word_count} words - Score: {self.overall_score}"

    @property
    def is_completed(self) -> bool:
        """Check if submission processing is completed."""
        return self.status == 'completed'

    @property
    def has_ai_analysis(self) -> bool:
        """Check if AI analysis is available."""
        return self.ai_analysis_data is not None

    @property
    def has_scores(self) -> bool:
        """Check if IELTS scores are available."""
        return self.overall_score is not None

    def get_score_summary(self) -> dict:
        """Get summary of all scores."""
        return {
            'task_achievement': float(self.task_achievement_score) if self.task_achievement_score else None,
            'coherence_cohesion': float(self.coherence_cohesion_score) if self.coherence_cohesion_score else None,
            'lexical_resource': float(self.lexical_resource_score) if self.lexical_resource_score else None,
            'grammatical_accuracy': float(self.grammatical_accuracy_score) if self.grammatical_accuracy_score else None,
            'overall': float(self.overall_score) if self.overall_score else None
        }

    def get_analysis_summary(self) -> dict:
        """Get summary of analysis metrics."""
        return {
            'readability_score': float(self.readability_score) if self.readability_score else None,
            'lexical_diversity': float(self.lexical_diversity) if self.lexical_diversity else None,
            'sentence_complexity': float(self.sentence_complexity_score) if self.sentence_complexity_score else None,
            'structure_quality': float(self.structure_quality_score) if self.structure_quality_score else None,
            'overall_quality': self.overall_quality,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None
        }

    def to_dict(self, include_text: bool = False, include_analysis: bool = True) -> dict:
        """
        Convert submission to dictionary.

        Args:
            include_text: Whether to include full submission text
            include_analysis: Whether to include analysis data

        Returns:
            dict: Submission data
        """
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'task_type': self.task_type,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'submission_date': self.submission_date.isoformat() if self.submission_date else None,
            'status': self.status,
            'processing_time_seconds': self.processing_time_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_text:
            result['submission_text'] = self.submission_text
            result['feedback_text'] = self.feedback_text

        if include_analysis:
            result.update({
                'scores': self.get_score_summary(),
                'analysis': self.get_analysis_summary(),
                'content_stats': {
                    'sentence_count': self.sentence_count,
                    'paragraph_count': self.paragraph_count,
                    'academic_words_count': self.academic_words_count,
                    'transition_words_count': self.transition_words_count,
                    'recommendations_count': self.recommendations_count
                }
            })

        return result