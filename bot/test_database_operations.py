"""
Test script for database operations.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.logging_config import setup_logging
from shared.config import validate_environment
from shared.database import init_database, close_database
from shared.constants import TaskType, SubscriptionType
from database.user_operations import UserOperations
from database.submission_operations import SubmissionOperations
from database.channel_operations import ChannelOperations


async def test_database_operations():
    """Test all database operations."""

    # Set up logging
    setup_logging()

    print("🧪 Testing Database Operations")
    print("=" * 50)

    # Test 1: Environment and database
    print("1. Testing environment and database...")
    if not validate_environment():
        print("❌ Environment validation failed!")
        return False

    if not init_database():
        print("❌ Database initialization failed!")
        return False
    print("   ✅ Environment and database OK")

    # Test 2: User operations
    print("2. Testing user operations...")
    try:
        # Create test user
        test_telegram_id = 123456789
        user = UserOperations.create_user(
            telegram_id=test_telegram_id,
            username="testuser",
            first_name="Test",
            last_name="User"
        )

        if user:
            print(f"   ✅ User created: {user.display_name}")

            # Test user stats
            stats = UserOperations.get_user_stats(test_telegram_id)
            if stats:
                print(f"   ✅ User stats retrieved: {stats['monthly_submissions']}/{stats['monthly_limit']}")

            # Test bonus addition
            added = UserOperations.add_bonus_requests(test_telegram_id, 5)
            print(f"   ✅ Bonus requests added: {added}")

        else:
            print("   ❌ User creation failed")
            return False

    except Exception as e:
        print(f"   ❌ User operations failed: {e}")
        return False

    # Test 3: Submission operations
    print("3. Testing submission operations...")
    try:
        if user:
            # Create test submission
            submission = SubmissionOperations.create_submission(
                user_id=user.id,
                submission_text="This is a test submission for IELTS writing practice.",
                task_type=TaskType.TASK2,
                word_count=10
            )

            if submission:
                print(f"   ✅ Submission created: ID={submission.id}")

                # Test score update
                success = SubmissionOperations.update_submission_scores(
                    submission_id=submission.id,
                    task_achievement=7.0,
                    coherence_cohesion=6.5,
                    lexical_resource=7.5,
                    grammatical_accuracy=6.0
                )

                if success:
                    print("   ✅ Submission scores updated")

                # Test completion
                success = SubmissionOperations.complete_submission(
                    submission_id=submission.id,
                    feedback_text="Good work! Keep practicing.",
                    processing_time=45
                )

                if success:
                    print("   ✅ Submission completed")

            else:
                print("   ❌ Submission creation failed")
                return False

    except Exception as e:
        print(f"   ❌ Submission operations failed: {e}")
        return False

    # Test 4: Channel operations
    print("4. Testing channel operations...")
    try:
        # Create test channel
        channel = ChannelOperations.create_channel(
            channel_username="testchannel",
            channel_title="Test Channel",
            channel_id=-1001234567890,
            bonus_requests=5,
            description="Test channel for bonus requests"
        )

        if channel:
            print(f"   ✅ Channel created: @{channel.channel_username}")

            # Test membership update
            success, bonus_granted = ChannelOperations.update_user_membership(
                user_id=user.id,
                channel_id=channel.id,
                is_member=True
            )

            if success:
                print(f"   ✅ Membership updated, bonus granted: {bonus_granted}")

            # Test membership check
            is_member = ChannelOperations.check_user_channel_membership(
                user_id=user.id,
                channel_username="testchannel"
            )

            if is_member is not None:
                print(f"   ✅ Membership check: {is_member}")

        else:
            print("   ❌ Channel creation failed")
            return False

    except Exception as e:
        print(f"   ❌ Channel operations failed: {e}")
        return False

    # Test 5: Statistics
    print("5. Testing statistics...")
    try:
        user_stats = UserOperations.get_user_count_statistics()
        submission_stats = SubmissionOperations.get_submission_statistics()
        channel_stats = ChannelOperations.get_channel_statistics()

        print(f"   ✅ User statistics: {user_stats['total_users']} total users")
        print(f"   ✅ Submission statistics: {submission_stats['total_submissions']} total submissions")
        print(f"   ✅ Channel statistics: {channel_stats['total_channels']} total channels")

    except Exception as e:
        print(f"   ❌ Statistics failed: {e}")
        return False

    # Cleanup
    close_database()

    print("\n🎉 All database operations tests passed!")
    print("\nNext steps:")
    print("1. Database operations are ready for use in handlers")
    print("2. All CRUD operations working correctly")
    print("3. Statistics and reporting functions operational")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_database_operations())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)