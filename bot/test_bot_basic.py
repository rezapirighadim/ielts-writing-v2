"""
Basic bot test script to verify bot configuration and connection.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.logging_config import setup_logging
from config.bot_config import bot_config
from shared.config import validate_environment


async def test_bot_basic():
    """Test basic bot configuration and connection."""

    # Set up logging
    setup_logging()

    print("🧪 Testing Bot Basic Configuration")
    print("=" * 50)

    # Test 1: Environment validation
    print("1. Testing environment validation...")
    if not validate_environment():
        print("❌ Environment validation failed!")
        return False
    print("   ✅ Environment OK")

    # Test 2: Bot token validation
    print("2. Testing bot token...")
    if not bot_config.validate_token():
        print("❌ Bot token validation failed!")
        return False
    print("   ✅ Bot token valid")

    # Test 3: Create application
    print("3. Testing application creation...")
    try:
        application = bot_config.create_application()
        print("   ✅ Application created successfully")
    except Exception as e:
        print(f"❌ Application creation failed: {e}")
        return False

    # Test 4: Test bot connection
    print("4. Testing bot connection...")
    try:
        await application.initialize()
        bot = application.bot

        # Get bot info
        bot_info = await bot.get_me()
        print(f"   ✅ Connected to bot: @{bot_info.username}")
        print(f"   📊 Bot ID: {bot_info.id}")
        print(f"   👤 Bot Name: {bot_info.first_name}")

        # Cleanup
        await application.shutdown()

    except Exception as e:
        print(f"❌ Bot connection test failed: {e}")
        return False

    print("\n🎉 All basic bot tests passed!")
    print("\nNext steps:")
    print("1. Add your bot token to .env file if not already done")
    print("2. Make sure your bot is configured with @BotFather")
    print("3. Ready to add command handlers!")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_bot_basic())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)