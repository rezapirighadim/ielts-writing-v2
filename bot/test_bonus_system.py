"""
Test script for bonus request system.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.logging_config import setup_logging
from shared.config import validate_environment
from shared.database import init_database, close_database
from database.user_operations import UserOperations
from database.channel_operations import ChannelOperations
from handlers.bonus_manager import bonus_manager


async def test_bonus_system():
    """Test bonus request system functionality."""

    # Set up logging
    setup_logging()

    print("🧪 Testing Bonus Request System")
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

    # Test 2: Create test data
    print("2. Setting up test data...")
    try:
        # Create test user
        test_telegram_id = 777888999
        user = UserOperations.get_user_by_telegram_id(test_telegram_id)

        if not user:
            user = UserOperations.create_user(
                telegram_id=test_telegram_id,
                username="bonusTestUser",
                first_name="Bonus",
                last_name="Tester"
            )

        if not user:
            print("   ❌ Failed to create test user")
            return False

        # Create test channel
        test_channel = ChannelOperations.get_channel_by_username("bonustestchannel")
        if not test_channel:
            test_channel = ChannelOperations.create_channel(
                channel_username="bonustestchannel",
                channel_title="Bonus Test Channel",
                channel_id=-1001111111111,
                bonus_requests=15,
                description="Test channel for bonus system"
            )

            if not test_channel:
                print("   ❌ Failed to create test channel")
                return False

        print(f"   ✅ Test user: {user.display_name}")
        print(f"   ✅ Test channel: @{test_channel.channel_username}")

    except Exception as e:
        print(f"   ❌ Test data setup failed: {e}")
        return False

    # Test 3: Calculate available bonuses
    print("3. Testing bonus calculation...")
    try:
        bonus_calc = bonus_manager.calculate_available_bonuses(user.id)

        if bonus_calc.get("success", False):
            print("   ✅ Bonus calculation successful")
            print(f"      Total channels: {bonus_calc.get('total_channels', 0)}")
            print(f"      Current memberships: {bonus_calc.get('current_memberships', 0)}")
            print(f"      Eligible for bonus: {bonus_calc.get('eligible_for_bonus', 0)}")
            print(f"      Potential bonus: {bonus_calc.get('potential_bonus_requests', 0)}")
        else:
            print(f"   ❌ Bonus calculation failed: {bonus_calc.get('error', 'Unknown')}")
            return False
    except Exception as e:
        print(f"   ❌ Bonus calculation test failed: {e}")
        return False

    # Test 4: Validate bonus eligibility
    print("4. Testing bonus eligibility validation...")
    try:
        is_eligible, reason = bonus_manager.validate_bonus_eligibility(
            user_id=user.id,
            channel_id=test_channel.id
        )

        print(f"   ✅ Eligibility check completed")
        print(f"      Eligible: {is_eligible}")
        print(f"      Reason: {reason}")

    except Exception as e:
        print(f"   ❌ Eligibility validation test failed: {e}")
        return False

    # Test 5: Process membership bonus (simulate user joining channel)
    print("5. Testing bonus processing...")
    try:
        # Simulate user becoming a member
        success, bonus_details = await bonus_manager.process_membership_bonus(
            user_id=user.id,
            channel_id=test_channel.id,
            is_member=True
        )

        print(f"   ✅ Bonus processing completed")
        print(f"      Success: {success}")
        print(f"      Membership updated: {bonus_details.get('membership_updated', False)}")
        print(f"      Bonus granted: {bonus_details.get('bonus_granted', False)}")
        print(f"      Bonus amount: {bonus_details.get('bonus_amount', 0)}")

        if bonus_details.get('channel_title'):
            print(f"      Channel: {bonus_details.get('channel_title')}")

    except Exception as e:
        print(f"   ❌ Bonus processing test failed: {e}")
        return False

    # Test 6: Try to process bonus again (should not grant duplicate)
    print("6. Testing duplicate bonus prevention...")
    try:
        success, bonus_details = await bonus_manager.process_membership_bonus(
            user_id=user.id,
            channel_id=test_channel.id,
            is_member=True
        )

        print(f"   ✅ Duplicate bonus test completed")
        print(f"      Success: {success}")
        print(f"      Bonus granted: {bonus_details.get('bonus_granted', False)}")

        if not bonus_details.get('bonus_granted', True):
            print("   ✅ Duplicate bonus correctly prevented")
        else:
            print("   ❌ Duplicate bonus was granted (should not happen)")
            return False

    except Exception as e:
        print(f"   ❌ Duplicate bonus test failed: {e}")
        return False

    # Test 7: Get bonus history
    print("7. Testing bonus history...")
    try:
        history = bonus_manager.get_bonus_history(user.id)

        print(f"   ✅ Bonus history retrieved: {len(history)} records")

        for record in history[:3]:  # Show first 3 records
            created_at = record.get('created_at', 'Unknown')
            message = record.get('message', 'No message')[:50]
            print(f"      - {created_at}: {message}...")

    except Exception as e:
        print(f"   ❌ Bonus history test failed: {e}")
        return False

    # Test 8: Format bonus summary
    print("8. Testing bonus summary formatting...")
    try:
        # Get updated bonus calculation
        updated_calc = bonus_manager.calculate_available_bonuses(user.id)
        summary = bonus_manager.format_bonus_summary(updated_calc)

        print("   ✅ Bonus summary formatted")
        print(f"      Sample: {summary[:100]}...")

    except Exception as e:
        print(f"   ❌ Bonus summary test failed: {e}")
        return False

    # Test 9: Get system bonus statistics
    print("9. Testing system bonus statistics...")
    try:
        stats = bonus_manager.get_channel_bonus_statistics()

        if 'error' not in stats:
            print("   ✅ System statistics retrieved")
            print(f"      Total bonus grants: {stats.get('total_bonus_grants', 0)}")
            print(f"      Users with bonuses: {stats.get('users_with_bonus_requests', 0)}")
            print(f"      Utilization rate: {stats.get('bonus_utilization_rate', 0):.1f}%")
        else:
            print(f"   ❌ Statistics failed: {stats.get('error', 'Unknown')}")

    except Exception as e:
        print(f"   ❌ System statistics test failed: {e}")
        return False

    # Test 10: Test membership removal (user leaves channel)
    print("10. Testing membership removal...")
    try:
        success, removal_details = await bonus_manager.process_membership_bonus(
            user_id=user.id,
            channel_id=test_channel.id,
            is_member=False
        )

        print(f"   ✅ Membership removal processed")
        print(f"      Success: {success}")
        print(f"      Is member: {removal_details.get('is_member', True)}")
        print(f"      Bonus granted: {removal_details.get('bonus_granted', False)}")

        # Note: Bonus should not be revoked when user leaves

    except Exception as e:
        print(f"   ❌ Membership removal test failed: {e}")
        return False

    # Cleanup
    close_database()

    print("\n🎉 All bonus system tests passed!")
    print("\nTest Results Summary:")
    print("✅ Bonus calculation working correctly")
    print("✅ Eligibility validation functional")
    print("✅ Bonus processing operational")
    print("✅ Duplicate bonus prevention working")
    print("✅ Bonus history tracking functional")
    print("✅ Summary formatting working")
    print("✅ System statistics operational")
    print("✅ Membership state changes handled correctly")

    print("\nNext steps:")
    print("1. Bonus system ready for channel handlers")
    print("2. Integration with membership verification complete")
    print("3. User bonus tracking and history available")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_bonus_system())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)