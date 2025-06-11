"""
Test script for basic bot handlers.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.logging_config import setup_logging
from config.bot_config import bot_config
from shared.config import validate_environment
from shared.database import init_database, close_database
from handlers.basic_handlers import register_basic_handlers
from handlers.error_handler import register_error_handler


async def test_handlers():
    """Test that handlers can be registered without errors."""

    # Set up logging
    setup_logging()

    print("🧪 Testing Bot Handlers")
    print("=" * 50)

    # Test 1: Environment validation
    print("1. Testing environment...")
    if not validate_environment():
        print("❌ Environment validation failed!")
        return False
    print("   ✅ Environment OK")

    # Test 2: Database connection
    print("2. Testing database connection...")
    if not init_database():
        print("❌ Database connection failed!")
        return False
    print("   ✅ Database connected")

    # Test 3: Create application
    print("3. Testing application creation...")
    try:
        application = bot_config.create_application()
        print("   ✅ Application created")
    except Exception as e:
        print(f"❌ Application creation failed: {e}")
        return False

    # Test 4: Register handlers
    print("4. Testing handler registration...")
    try:
        register_basic_handlers(application)
        print("   ✅ Basic handlers registered")

        register_error_handler(application)
        print("   ✅ Error handler registered")

    except Exception as e:
        print(f"❌ Handler registration failed: {e}")
        return False

    # Test 5: Check registered handlers
    print("5. Verifying registered handlers...")
    handlers = application.handlers
    print(f"   📊 Total handler groups: {len(handlers)}")

    for group_id, group_handlers in handlers.items():
        print(f"   Group {group_id}: {len(group_handlers)} handlers")
        for handler in group_handlers:
            print(f"     - {type(handler).__name__}")

    # Cleanup
    close_database()

    print("\n🎉 All handler tests passed!")
    print("\nNext steps:")
    print("1. Start the bot with: python main.py")
    print("2. Test /start and /help commands")
    print("3. Check that user registration works")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_handlers())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)