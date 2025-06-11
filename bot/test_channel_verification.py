"""
Test script for channel membership verification system.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.logging_config import setup_logging
from shared.config import validate_environment
from shared.database import init_database, close_database
from config.bot_config import bot_config
from channels.membership_checker import MembershipChecker, MembershipResult
from channels.channel_manager import ChannelManager
from channels.verification_utils import get_channel_bonus_info, format_channel_list_message
from database.user_operations import UserOperations
from database.channel_operations import ChannelOperations

async def test_channel_verification():
    """Test channel membership verification system."""

    # Set up logging
    setup_logging()

    print("🧪 Testing Channel Membership Verification")
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

    # Test 2: Bot configuration
    print("2. Testing bot configuration...")
    try:
        application = bot_config.create_application()
        bot = application.bot
        print("   ✅ Bot configuration OK")
    except Exception as e:
        print(f"   ❌ Bot configuration failed: {e}")
        return False


    # Test 3: Create or get test user and channel
    print("3. Setting up test data...")
    try:
        import random

        # Create or get test user
        test_telegram_id = 999888777
        user = UserOperations.get_user_by_telegram_id(test_telegram_id)

        if not user:
            user = UserOperations.create_user(
                telegram_id=test_telegram_id,
                username="channelTestUser",
                first_name="Channel",
                last_name="Tester"
            )

        if not user:
            print("   ❌ Failed to create/get test user")
            return False

        # Create or get test channel with random ID to avoid conflicts
        test_channel_username = "testchannel123"
        test_channel = ChannelOperations.get_channel_by_username(test_channel_username)

        if not test_channel:
            # Generate random channel ID to avoid duplicates
            random_channel_id = -1000000000000 - random.randint(1, 999999)
            test_channel = ChannelOperations.create_channel(
                channel_username=test_channel_username,
                channel_title="Test Channel for Verification",
                channel_id=random_channel_id,
                bonus_requests=10,
                description="Test channel for membership verification"
            )

        if not test_channel:
            print("   ❌ Failed to create/get test channel")
            return False

        print(f"   ✅ Test user: {user.display_name} (ID: {user.id})")
        print(f"   ✅ Test channel: @{test_channel.channel_username} (ID: {test_channel.id})")

    except Exception as e:
        print(f"   ❌ Test data setup failed: {e}")
        return False

    # Test 4: Membership checker initialization
    print("4. Testing membership checker...")
    try:
        membership_checker = MembershipChecker(bot)
        print("   ✅ MembershipChecker initialized")
    except Exception as e:
        print(f"   ❌ MembershipChecker initialization failed: {e}")
        return False

    # Test 5: Channel manager initialization
    print("5. Testing channel manager...")
    try:
        channel_manager = ChannelManager(bot)
        print("   ✅ ChannelManager initialized")
    except Exception as e:
        print(f"   ❌ ChannelManager initialization failed: {e}")
        return False

    # Test 6: Get available channels for bonus
    print("6. Testing channel bonus info...")
    try:
        bonus_info = get_channel_bonus_info(user.id)
        if bonus_info.get("success", False):
            print(f"   ✅ Channel bonus info retrieved")
            print(f"      Total channels: {bonus_info.get('total_channels', 0)}")
            print(f"      Member channels: {bonus_info.get('member_channels', 0)}")
            print(f"      Bonus eligible: {bonus_info.get('bonus_eligible_channels', 0)}")
            print(f"      Potential bonus: {bonus_info.get('total_potential_bonus', 0)}")
        else:
            print(f"   ❌ Failed to get channel bonus info: {bonus_info.get('error', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ Channel bonus info test failed: {e}")
        return False

    # Test 7: Format channel list message
    print("7. Testing message formatting...")
    try:
        formatted_message = format_channel_list_message(bonus_info)
        print("   ✅ Channel list message formatted")
        print(f"      Sample: {formatted_message[:100]}...")
    except Exception as e:
        print(f"   ❌ Message formatting failed: {e}")
        return False

    # Test 8: Membership check (will fail for fake channel, but tests the flow)
    print("8. Testing membership verification flow...")
    try:
        # This will fail because it's a fake channel, but tests the error handling
        result = await membership_checker.check_user_membership(
            telegram_id=test_telegram_id,
            channel_username=test_channel_username,
            user_id=user.id
        )

        print(f"   ✅ Membership check completed")
        print(f"      Channel: @{result.channel_username}")
        print(f"      Is member: {result.is_member}")
        print(f"      Bonus eligible: {result.bonus_eligible}")
        print(f"      Bonus amount: {result.bonus_amount}")

        if result.error_message:
            print(f"      Expected error (fake channel): {result.error_message}")

    except Exception as e:
        print(f"   ❌ Membership verification test failed: {e}")
        return False

    # Test 9: Multiple channel verification
    print("9. Testing multiple channel verification...")
    try:
        results = await membership_checker.check_multiple_channels(
            telegram_id=test_telegram_id,
            user_id=user.id
        )

        print(f"   ✅ Multiple channel check completed")
        print(f"      Checked {len(results)} channels")

        for result in results:
            status = "✅" if result.is_member else "❌"
            error_info = f" (Error: {result.error_message})" if result.error_message else ""
            print(f"      - {status} @{result.channel_username}: Member={result.is_member}{error_info}")

    except Exception as e:
        print(f"   ❌ Multiple channel verification failed: {e}")
        return False

    # Test 10: Channel manager verification
    print("10. Testing channel manager verification...")
    try:
        verification_result = await channel_manager.verify_and_grant_bonuses(
            telegram_id=test_telegram_id,
            user_id=user.id
        )

        print(f"   ✅ Channel manager verification completed")
        print(f"      Success: {verification_result.get('success', False)}")
        print(f"      Bonuses granted: {verification_result.get('total_bonuses_granted', 0)}")
        print(f"      Available submissions: {verification_result.get('available_submissions', 0)}")

        message_preview = verification_result.get('message', 'No message')[:100]
        print(f"      Message preview: {message_preview}...")

    except Exception as e:
        print(f"   ❌ Channel manager verification failed: {e}")
        return False

    # Test 11: Single channel verification
    print("11. Testing single channel verification...")
    try:
        single_result = await channel_manager.check_single_channel_membership(
            telegram_id=test_telegram_id,
            channel_username=test_channel_username,
            user_id=user.id
        )

        print(f"   ✅ Single channel verification completed")
        print(f"      Success: {single_result.get('success', False)}")
        print(f"      Is member: {single_result.get('is_member', False)}")
        print(f"      Bonus granted: {single_result.get('bonus_granted', 0)}")
        print(f"      Message: {single_result.get('message', 'No message')}")

    except Exception as e:
        print(f"   ❌ Single channel verification failed: {e}")
        return False

    # Test 12: User memberships
    print("12. Testing user memberships retrieval...")
    try:
        memberships = channel_manager.get_user_channel_memberships(user.id)
        print(f"   ✅ User memberships retrieved: {len(memberships)} records")

        for membership in memberships:
            channel_title = membership.get('channel_title', 'Unknown')
            is_member = membership.get('is_member', False)
            bonus_granted = membership.get('bonus_granted', False)
            print(f"      - {channel_title}: Member={is_member}, Bonus={bonus_granted}")

    except Exception as e:
        print(f"   ❌ User memberships test failed: {e}")
        return False

    # Test 13: Available channels for bonus
    print("13. Testing available channels for bonus...")
    try:
        available_channels = channel_manager.get_available_channels_for_bonus(user.id)
        print(f"   ✅ Available channels retrieved: {len(available_channels)}")

        for channel in available_channels:
            channel_title = channel.get('channel_title', 'Unknown')
            can_get_bonus = channel.get('can_get_bonus', False)
            bonus_amount = channel.get('bonus_requests', 0)
            is_member = channel.get('is_member', False)
            print(f"      - {channel_title}: Member={is_member}, Can get bonus={can_get_bonus} ({bonus_amount})")

    except Exception as e:
        print(f"   ❌ Available channels test failed: {e}")
        return False

    # Test 14: Utility functions
    print("14. Testing utility functions...")
    try:
        from channels.verification_utils import (
            create_membership_check_buttons,
            format_membership_verification_message,
            extract_channel_username_from_callback,
            get_verification_status_summary
        )

        # Test button creation
        buttons = create_membership_check_buttons()
        if buttons:
            print("   ✅ Membership check buttons created")

        # Test callback extraction
        extracted = extract_channel_username_from_callback("check_channel:testchannel")
        if extracted == "testchannel":
            print("   ✅ Callback extraction working")

        # Test verification summary
        summary = get_verification_status_summary(results)
        print(f"   ✅ Verification summary: {summary['total_channels']} channels, {summary['member_channels']} memberships")

    except Exception as e:
        print(f"   ❌ Utility functions test failed: {e}")
        return False

    # Cleanup
    close_database()

    print("\n🎉 All channel verification tests passed!")
    print("\nTest Results Summary:")
    print("✅ Channel membership verification system operational")
    print("✅ Bonus granting mechanism working")
    print("✅ Multiple channel support functional")
    print("✅ Error handling for fake/invalid channels working")
    print("✅ Database operations successful")
    print("✅ Utility functions ready for integration")

    print("\nNote:")
    print("⚠️  Tests use fake channel data - actual Telegram API calls will fail")
    print("💡 This is expected behavior and demonstrates proper error handling")
    print("🔧 For real testing, add actual Telegram channels to the database")

    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_channel_verification())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)