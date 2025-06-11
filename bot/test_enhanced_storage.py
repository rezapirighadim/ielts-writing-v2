#!/usr/bin/env python3
"""
Test script for enhanced submission storage system.
"""

import sys
import os
import json
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import database initialization
from shared.database import init_database, close_database
from shared.config import validate_environment
from config.logging_config import setup_logging

from database.enhanced_submission_operations import EnhancedSubmissionOperations
from handlers.text_validators import validate_submission_text
from database.user_operations import UserOperations

# Set up logging
setup_logging()


def create_test_user():
    """Create a test user for submission testing."""
    print("👤 Creating test user...")

    test_telegram_id = 999999999
    test_username = 'test_enhanced_storage'
    test_first_name = 'Test'
    test_last_name = 'Enhanced'

    # Try to get existing user first
    existing_user = UserOperations.get_user_by_telegram_id(test_telegram_id)
    if existing_user:
        print(f"   ✅ Using existing test user: {existing_user.id}")
        return existing_user.id

    # Create new user using the correct function signature
    user = UserOperations.create_user(
        telegram_id=test_telegram_id,
        username=test_username,
        first_name=test_first_name,
        last_name=test_last_name
    )

    if user:
        print(f"   ✅ Test user created with ID: {user.id}")
        return user.id
    else:
        print("   ❌ Failed to create test user")
        return None


def test_enhanced_submission_creation():
    """Test creating submissions with enhanced data."""
    print("\n📝 Testing enhanced submission creation...")

    # Create test user
    user_id = create_test_user()
    if not user_id:
        print("   ❌ Cannot test without user")
        return False

    # Sample Task 2 text
    sample_text = """
    In today's digital age, the debate about whether technology has improved or worsened 
    human communication has become increasingly relevant. While technology has undoubtedly 
    revolutionized the way we connect with others, its impact on the quality of human 
    relationships remains a contentious issue.

    Proponents of digital communication argue that technology has broken down geographical 
    barriers and enabled people to maintain relationships across vast distances. Social 
    media platforms, video calling applications, and instant messaging services have made 
    it possible for families and friends to stay connected regardless of physical separation. 
    Furthermore, online communities have allowed individuals with shared interests to form 
    meaningful connections that might not have been possible in the pre-digital era.

    However, critics contend that excessive reliance on digital communication has led to 
    a deterioration in the quality of human interactions. They argue that face-to-face 
    communication provides emotional nuances and non-verbal cues that are lost in digital 
    exchanges. Additionally, the prevalence of social media has been linked to increased 
    feelings of isolation and anxiety, particularly among younger generations.

    In conclusion, while technology has expanded our ability to communicate and connect 
    with others, it is essential to maintain a balance between digital and in-person 
    interactions to preserve the authenticity and depth of human relationships.
    """

    try:
        # Validate the text to get analysis data
        validation_result = validate_submission_text(sample_text.strip(), 'task2')

        # Extract analysis components
        word_count_analysis = validation_result.get('word_count_analysis')
        text_analysis = validation_result.get('text_analysis')

        # Prepare enhanced submission data
        submission_data = {
            'user_id': user_id,
            'telegram_id': 999999999,
            'submission_text': sample_text.strip(),
            'task_type': 'task2',
            'word_count': validation_result['word_count'],
            'character_count': validation_result['character_count'],
            'submission_date': datetime.utcnow(),
            'status': 'pending',

            # Enhanced validation data
            'word_count_analysis': word_count_analysis.__dict__ if hasattr(word_count_analysis,
                                                                           '__dict__') else word_count_analysis,
            'text_analysis': text_analysis.__dict__ if hasattr(text_analysis, '__dict__') else text_analysis,
            'language_analysis': validation_result.get('language_analysis', {}),
            'quality_analysis': validation_result.get('quality_analysis', {}),
            'validation_method': 'test_enhanced_v1',

            # Extract metrics
            'readability_score': getattr(text_analysis, 'readability_score', 50) if text_analysis else 50,
            'overall_quality': getattr(text_analysis, 'overall_quality', 'good') if text_analysis else 'good',
            'confidence_score': getattr(word_count_analysis, 'confidence_score', 0.95) if word_count_analysis else 0.95,

            # Content statistics
            'sentence_count': 8,
            'paragraph_count': 4,
            'lexical_diversity': 0.65,
            'academic_words_count': 12,
            'complexity_score': 0.75,
            'structure_score': 0.85,
            'recommendations_count': 3
        }

        # Create enhanced submission
        submission_id = EnhancedSubmissionOperations.create_enhanced_submission(submission_data)

        if submission_id:
            print(f"   ✅ Enhanced submission created with ID: {submission_id}")
            print(f"   📊 Word count: {validation_result['word_count']}")
            print(f"   🎯 Overall quality: {submission_data['overall_quality']}")
            print(f"   📈 Confidence: {submission_data['confidence_score']:.1%}")
            return submission_id
        else:
            print("   ❌ Failed to create enhanced submission")
            return None

    except Exception as e:
        print(f"   ❌ Error creating enhanced submission: {e}")
        return None


def test_submission_retrieval(submission_id):
    """Test retrieving submission with analysis data."""
    print(f"\n📖 Testing submission retrieval for ID {submission_id}...")

    try:
        # Get submission with full analysis
        submission_data = EnhancedSubmissionOperations.get_submission_with_analysis(submission_id)

        if not submission_data:
            print("   ❌ Submission not found")
            return False

        print(f"   ✅ Submission retrieved successfully")
        print(f"   📝 Task type: {submission_data['task_type']}")
        print(f"   📊 Word count: {submission_data['word_count']}")
        print(f"   📅 Submission date: {submission_data['submission_date']}")
        print(f"   🔧 Status: {submission_data['status']}")

        # Check validation data
        validation_data = submission_data.get('validation_data', {})
        if validation_data:
            print(f"   🔍 Validation data keys: {list(validation_data.keys())}")

        # Check analysis metadata
        analysis_metadata = submission_data.get('analysis_metadata', {})
        if analysis_metadata:
            print(f"   📊 Analysis metadata keys: {list(analysis_metadata.keys())}")
            print(f"   🎯 Readability: {analysis_metadata.get('readability_score', 'N/A')}")
            print(f"   📈 Overall quality: {analysis_metadata.get('overall_quality', 'N/A')}")

        return True

    except Exception as e:
        print(f"   ❌ Error retrieving submission: {e}")
        return False


def test_submission_analysis_update(submission_id):
    """Test updating submission with AI analysis results."""
    print(f"\n🤖 Testing AI analysis update for submission {submission_id}...")

    # Mock AI analysis results
    ai_analysis_data = {
        'task_achievement_score': 7.5,
        'coherence_cohesion_score': 7.0,
        'lexical_resource_score': 6.5,
        'grammatical_accuracy_score': 7.0,
        'overall_score': 7.0,
        'feedback_text': 'This is a well-structured essay with clear arguments and good use of vocabulary.',
        'processing_time_seconds': 45,
        'status': 'completed',
        'ai_model_version': 'test_model_v1.0',
        'detailed_feedback': {
            'strengths': ['Clear thesis statement', 'Good paragraph structure', 'Appropriate examples'],
            'weaknesses': ['Some repetitive vocabulary', 'Could use more complex sentences'],
            'suggestions': ['Vary sentence structure more', 'Use more sophisticated vocabulary']
        },
        'scoring_breakdown': {
            'task_achievement': {'score': 7.5, 'reasoning': 'Addresses all parts of the task effectively'},
            'coherence_cohesion': {'score': 7.0, 'reasoning': 'Well-organized with clear progression'},
            'lexical_resource': {'score': 6.5, 'reasoning': 'Good range but some repetition'},
            'grammatical_accuracy': {'score': 7.0, 'reasoning': 'Generally accurate with minor errors'}
        }
    }

    try:
        success = EnhancedSubmissionOperations.update_submission_analysis(submission_id, ai_analysis_data)

        if success:
            print("   ✅ AI analysis updated successfully")

            # Retrieve updated submission
            updated_submission = EnhancedSubmissionOperations.get_submission_with_analysis(submission_id)
            if updated_submission:
                print(f"   🎯 Overall score: {updated_submission['overall_score']}")
                print(f"   ⏱️ Processing time: {updated_submission['processing_time_seconds']}s")
                print(f"   🔧 Status: {updated_submission['status']}")

                # Check AI analysis data
                ai_data = updated_submission.get('ai_analysis_data', {})
                if ai_data:
                    print(f"   🤖 AI model: {ai_data.get('ai_model_version', 'N/A')}")
                    strengths = ai_data.get('detailed_feedback', {}).get('strengths', [])
                    print(f"   💪 Strengths count: {len(strengths)}")

            return True
        else:
            print("   ❌ Failed to update AI analysis")
            return False

    except Exception as e:
        print(f"   ❌ Error updating AI analysis: {e}")
        return False


def test_user_submissions_stats():
    """Test getting user submissions with statistics."""
    print("\n📊 Testing user submissions statistics...")

    user_id = create_test_user()
    if not user_id:
        return False

    try:
        # Get user submissions with stats
        submissions = EnhancedSubmissionOperations.get_user_submissions_with_stats(
            user_id=user_id,
            limit=5,
            include_analysis=True
        )

        if submissions:
            print(f"   ✅ Found {len(submissions)} submissions for user")

            for i, sub in enumerate(submissions, 1):
                print(f"   📝 Submission {i}:")
                print(f"      Task: {sub['task_type']}")
                print(f"      Words: {sub['word_count']}")
                print(f"      Score: {sub.get('overall_score', 'N/A')}")
                print(f"      Quality: {sub.get('overall_quality', 'N/A')}")
                print(f"      Date: {sub['submission_date']}")
        else:
            print("   ℹ️ No submissions found for user")

        return True

    except Exception as e:
        print(f"   ❌ Error getting user submission stats: {e}")
        return False


def test_submission_analytics():
    """Test submission analytics functionality."""
    print("\n📈 Testing submission analytics...")

    user_id = create_test_user()
    if not user_id:
        return False

    try:
        # Get analytics for the user
        analytics = EnhancedSubmissionOperations.get_submission_analytics(
            user_id=user_id,
            days_back=30
        )

        print(f"   ✅ Analytics retrieved successfully")
        print(f"   📊 Total submissions: {analytics.get('total_submissions', 0)}")
        print(f"   ✅ Completed submissions: {analytics.get('completed_submissions', 0)}")

        # Average scores
        avg_scores = analytics.get('average_scores', {})
        if avg_scores:
            print(f"   🎯 Average scores available for {len(avg_scores)} categories")
            for score_type, score_data in avg_scores.items():
                if score_data:
                    print(f"      {score_type}: {score_data.get('average', 0):.1f}")

        # Word count stats
        word_stats = analytics.get('word_count_stats', {})
        if word_stats:
            print(f"   📏 Word count stats:")
            print(f"      Average: {word_stats.get('average', 0)} words")
            print(f"      Range: {word_stats.get('min', 0)}-{word_stats.get('max', 0)}")

        # Quality distribution
        quality_dist = analytics.get('quality_distribution', {})
        if quality_dist:
            print(f"   🏆 Quality distribution: {quality_dist}")

        # Task type breakdown
        task_breakdown = analytics.get('task_type_breakdown', {})
        if task_breakdown:
            print(f"   📝 Task type breakdown: {task_breakdown}")

        return True

    except Exception as e:
        print(f"   ❌ Error getting submission analytics: {e}")
        return False


def test_submission_search():
    """Test submission search functionality."""
    print("\n🔍 Testing submission search...")

    user_id = create_test_user()
    if not user_id:
        return False

    try:
        # Search for user's submissions
        search_results = EnhancedSubmissionOperations.search_submissions(
            user_id=user_id,
            task_type='task2',
            status='completed',
            limit=10
        )

        print(f"   ✅ Search completed")
        print(f"   📋 Found {len(search_results)} matching submissions")

        for result in search_results:
            print(f"      ID: {result['id']}, Type: {result['task_type']}, Score: {result.get('overall_score', 'N/A')}")

        # Test text search
        text_search_results = EnhancedSubmissionOperations.search_submissions(
            user_id=user_id,
            search_text='technology',
            limit=5
        )

        print(f"   🔍 Text search for 'technology': {len(text_search_results)} results")

        return True

    except Exception as e:
        print(f"   ❌ Error in submission search: {e}")
        return False


def test_json_serialization():
    """Test JSON serialization of complex objects."""
    print("\n🔧 Testing JSON serialization...")

    try:
        # Create sample complex data
        from handlers.word_count_validator import enhanced_word_counter
        from utils.text_analyzer import text_analyzer

        sample_text = "This is a test text for serialization testing purposes."

        # Get analysis objects
        word_result = enhanced_word_counter.validate_word_count(sample_text, 'task2')
        text_analysis = text_analyzer.perform_complete_analysis(sample_text, 'task2')

        # Test serialization
        word_dict = word_result.__dict__ if hasattr(word_result, '__dict__') else word_result
        text_dict = text_analysis.__dict__ if hasattr(text_analysis, '__dict__') else text_analysis

        # Try to serialize to JSON
        word_json = json.dumps(word_dict, default=str, ensure_ascii=False)
        text_json = json.dumps(text_dict, default=str, ensure_ascii=False)

        print(f"   ✅ Word count serialization successful ({len(word_json)} chars)")
        print(f"   ✅ Text analysis serialization successful ({len(text_json)} chars)")

        # Test deserialization
        word_restored = json.loads(word_json)
        text_restored = json.loads(text_json)

        print(f"   ✅ Deserialization successful")
        print(f"   📊 Word count keys: {len(word_restored.keys()) if isinstance(word_restored, dict) else 0}")
        print(f"   📋 Text analysis keys: {len(text_restored.keys()) if isinstance(text_restored, dict) else 0}")

        return True

    except Exception as e:
        print(f"   ❌ JSON serialization error: {e}")
        return False


def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")

    try:
        # Get test user - pass just the telegram_id integer
        test_telegram_id = 999999999
        test_user = UserOperations.get_user_by_telegram_id(test_telegram_id)
        if test_user:
            # Note: In a real cleanup, you might want to delete test submissions
            # For now, we'll just report what would be cleaned up
            submissions = EnhancedSubmissionOperations.get_user_submissions_with_stats(
                user_id=test_user.id,
                limit=100
            )

            print(f"   ℹ️ Found {len(submissions)} test submissions")
            print("   💡 Test data preserved for inspection")
            print(f"   👤 Test user ID: {test_user.id}")
        else:
            print("   ℹ️ No test user found")

        return True

    except Exception as e:
        print(f"   ❌ Cleanup error: {e}")
        return False


def run_all_enhanced_storage_tests():
    """Run all enhanced storage tests."""
    print("🚀 Starting enhanced submission storage tests...\n")

    # Initialize database first
    print("🔧 Initializing test environment...")
    if not validate_environment():
        print("❌ Environment validation failed")
        return False

    if not init_database():
        print("❌ Database initialization failed")
        return False

    print("✅ Database initialized successfully\n")

    test_results = []

    try:
        # Test JSON serialization first
        test_results.append(("JSON Serialization", test_json_serialization()))

        # Test submission creation
        submission_id = test_enhanced_submission_creation()
        test_results.append(("Enhanced Submission Creation", submission_id is not None))

        if submission_id:
            # Test retrieval
            test_results.append(("Submission Retrieval", test_submission_retrieval(submission_id)))

            # Test AI analysis update
            test_results.append(("AI Analysis Update", test_submission_analysis_update(submission_id)))

        # Test statistics and analytics
        test_results.append(("User Submission Stats", test_user_submissions_stats()))
        test_results.append(("Submission Analytics", test_submission_analytics()))
        test_results.append(("Submission Search", test_submission_search()))

        # Cleanup
        test_results.append(("Cleanup", cleanup_test_data()))

        # Summary
        print("\n📊 Test Results Summary:")
        passed = 0
        failed = 0

        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status} {test_name}")
            if result:
                passed += 1
            else:
                failed += 1

        print(f"\n🎯 Total: {passed} passed, {failed} failed")

        if failed == 0:
            print("\n🎉 All enhanced storage tests passed!")
        else:
            print(f"\n⚠️ {failed} tests failed - check implementation")

        print("\n✨ Enhanced Storage Features Tested:")
        print("   • Comprehensive validation data storage")
        print("   • Text analysis results preservation")
        print("   • AI evaluation data integration")
        print("   • User statistics and analytics")
        print("   • Advanced search and filtering")
        print("   • JSON serialization of complex objects")

        return failed == 0

    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Close database connections
        print("\n🔚 Closing database connections...")
        close_database()
        print("✅ Database connections closed")


if __name__ == "__main__":
    run_all_enhanced_storage_tests()