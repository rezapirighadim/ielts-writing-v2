"""
Test script for usage limit system.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.logging_config import setup_logging
from shared.config import validate_environment
from shared.database import init_database, close_database
from limits.usage_limiter import usage_limiter
from limits.limit_manager import limit_manager
from limits.limit_exceptions import LimitExceededException
from database.user_operations import UserOperations

async def test_usage_limits():
    """Test usage limit system functionality."""

    # Set up logging
    setup_logging()

    print("🧪 Testing Usage Limit System")
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

    # Test 2: Create test user
    print("2. Testing user creation...")
    try:
        test_telegram_id = 555666777
        user = UserOperations.create_user(
            telegram_id=test_telegram_id,
            username="limitTestUser",
            first_name="Limit",
            last_name="Tester"
        )

        if user:
            print(f"   ✅ Test user created: {user.display_name}")
        else:
            print("   ❌ User creation failed")
            return False
    except Exception as e:
        print(f"   ❌ User creation failed: {e}")
        return False

    # Test 3: Check initial limits
    print("3. Testing initial limit check...")
    try:
        limit_result = usage_limiter.check_submission_limit(test_telegram_id)
        print(f"   ✅ Initial limit check:")
        print(f"      Can proceed: {limit_result.can_proceed}")
        print(f"      Current usage: {limit_result.current_usage}")
        print(f"      Limit: {limit_result.limit}")
        print(f"      Available: {limit_result.available_submissions}")
        print(f"      Message: {limit_result.message}")
    except Exception as e:
        print(f"   ❌ Initial limit check failed: {e}")
        return False

    # Test 4: Consume submissions
    print("4. Testing submission consumption...")
    try:
        # Consume a few submissions
        for i in range(3):
            consumed = usage_limiter.consume_submission(test_telegram_id)
            if consumed:
                print(f"   ✅ Submission {i + 1} consumed")
            else:
                print(f"   ❌ Failed to consume submission {i + 1}")
                return False

        # Check updated limits
        updated_result = usage_limiter.check_submission_limit(test_telegram_id)
        print(f"   📊 After consumption - Available: {updated_result.available_submissions}")

    except Exception as e:
        print(f"   ❌ Submission consumption test failed: {e}")
        return False

    # Test 5: Add bonus requests
    print("5. Testing bonus requests...")
    try:
        bonus_added = usage_limiter.add_bonus_requests(
            telegram_id=test_telegram_id,
            amount=5,
            reason="Test channel membership"
        )

        if bonus_added > 0:
            print(f"   ✅ Bonus requests added: {bonus_added}")

            # Check updated limits
            bonus_result = usage_limiter.check_submission_limit(test_telegram_id)
            print(f"   📊 After bonus - Available: {bonus_result.available_submissions}")
            print(f"   💎 Bonus requests: {bonus_result.bonus_requests}")
        else:
            print("   ❌ Failed to add bonus requests")
            return False

    except Exception as e:
        print(f"   ❌ Bonus requests test failed: {e}")
        return False

    # Test 6: Limit manager operations
    print("6. Testing limit manager...")
    try:
        # Test can_user_submit
        can_submit, message = limit_manager.can_user_submit(test_telegram_id)
        print(f"   ✅ Can user submit: {can_submit}")
        print(f"   📝 Message: {message}")

        # Test submission request processing
        success, info = limit_manager.process_submission_request(test_telegram_id)
        print(f"   ✅ Process submission request: {success}")
        print(f"   📋 Info: {info}")

        # Test user limit summary
        summary = limit_manager.get_user_limit_summary(test_telegram_id)
        if 'error' not in summary:
            print(f"   ✅ User summary retrieved")
            print(f"      Usage: {summary.get('current_usage')}/{summary.get('monthly_limit')}")
            print(f"      Status: {summary.get('usage_label')}")
            print(f"      Available: {summary.get('available_submissions')}")
        else:
            print(f"   ❌ User summary failed: {summary['error']}")
            return False

    except Exception as e:
        print(f"   ❌ Limit manager test failed: {e}")
        return False

    # Test 7: Exceed limits
    print("7. Testing limit exceeded scenario...")
    try:
        # Consume all remaining submissions
        limit_result = usage_limiter.check_submission_limit(test_telegram_id)
        remaining = limit_result.available_submissions

        print(f"   📊 Consuming {remaining} remaining submissions...")

        for i in range(remaining):
            try:
                consumed = usage_limiter.consume_submission(test_telegram_id)
                if not consumed:
                    print(f"   ⚠️ Failed to consume submission {i + 1}")
                    break
            except LimitExceededException as e:
                print(f"   ✅ Limit exceeded as expected: {e}")
                break

        # Try to consume one more (should fail)
        try:
            usage_limiter.consume_submission(test_telegram_id)
            print("   ❌ Should have thrown LimitExceededException")
            return False
        except LimitExceededException:
            print("   ✅ Limit exceeded exception thrown correctly")

    except Exception as e:
        print(f"   ❌ Limit exceeded test failed: {e}")
        return False

    # Test 8: Premium upgrade
    print("8. Testing premium upgrade...")
    try:
        success = usage_limiter.upgrade_user_to_premium(test_telegram_id)
        if success:
            print("   ✅ User upgraded to premium")

            # Check new limits
            premium_result = usage_limiter.check_submission_limit(test_telegram_id)
            print(f"   💎 Premium limit: {premium_result.limit}")
            print(f"   📊 Available after upgrade: {premium_result.available_submissions}")
        else:
            print("   ❌ Premium upgrade failed")
            return False
    except Exception as e:
        print(f"   ❌ Premium upgrade test failed: {e}")
        return False

    # Test 9: Monthly reset
    print("9. Testing monthly reset...")
    try:
        success, message = limit_manager.reset_user_monthly_usage(test_telegram_id)
        if success:
            print(f"   ✅ Monthly reset successful: {message}")

            # Check reset limits
            reset_result = usage_limiter.check_submission_limit(test_telegram_id)
            print(f"   📊 After reset - Usage: {reset_result.current_usage}")
            print(f"   📊 Available: {reset_result.available_submissions}")
        else:
            print(f"   ❌ Monthly reset failed: {message}")
            return False
    except Exception as e:
        print(f"   ❌ Monthly reset test failed: {e}")
        return False

    # Test 10: System statistics
    print("10. Testing system statistics...")
    try:
        stats = limit_manager.get_system_limit_stats()
        if 'error' not in stats:
            print("   ✅ System statistics retrieved")
            print(f"      Total users: {stats['user_statistics']['total_users']}")
            print(f"      Users near limit: {stats['users_near_limit']}")
            print(f"      Cache entries: {stats['cache_stats']['cached_entries']}")
        else:
            print(f"   ❌ System statistics failed: {stats['error']}")
            return False
    except Exception as e:
        print(f"   ❌ System statistics test failed: {e}")
        return False

    # Test 11: Limit utility functions
    print("11. Testing limit utilities...")
    try:
        from limits.limit_utils import format_limit_message, format_limit_exceeded_message

        # Test message formatting
        limit_info = limit_manager.get_user_limit_summary(test_telegram_id)
        formatted_message = format_limit_message(limit_info)
        print(f"   ✅ Limit message formatted")
        print(f"      Sample: {formatted_message[:100]}...")

        # Test exceeded message
        exceeded_message = format_limit_exceeded_message(limit_info)
        print(f"   ✅ Exceeded message formatted")
        print(f"      Sample: {exceeded_message[:100]}...")

    except Exception as e:
        print(f"   ❌ Limit utilities test failed: {e}")
        return False

    # Test 12: Cache functionality
    print("12. Testing cache functionality...")
    try:
        # Check cache stats
        cache_stats = usage_limiter.get_cache_stats()
        print(f"   ✅ Cache stats: {cache_stats}")

        # Clear cache
        usage_limiter.clear_all_cache()
        print("   ✅ Cache cleared")

        # Verify cache is empty
        empty_cache_stats = usage_limiter.get_cache_stats()
        if empty_cache_stats['cached_entries'] == 0:
            print("   ✅ Cache successfully cleared")
        else:
            print("   ❌ Cache not properly cleared")
            return False

    except Exception as e:
        print(f"   ❌ Cache test failed: {e}")
        return False

    # Cleanup
    close_database()

    print("\n🎉 All usage limit tests passed!")
    print("\nNext steps:")
    print("1. Usage limit system is ready for integration")
    print("2. Monthly limits enforced correctly")
    print("3. Bonus requests and premium upgrades working")
    print("4. Comprehensive limit management available")
    print("5. Cache optimization functioning properly")
    print("6. Utility functions ready for handler use")

    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_usage_limits())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)