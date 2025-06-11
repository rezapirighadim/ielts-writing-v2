"""
Test script to verify all imports work correctly.
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all models can be imported correctly."""
    print("Testing imports...")

    try:
        print("1. Importing database base...")
        from shared.database import Base
        print("   ✅ Base imported")

        print("2. Importing individual models...")
        from shared.models.user import User
        print("   ✅ User imported")

        from shared.models.submission import Submission
        print("   ✅ Submission imported")

        from shared.models.admin_user import AdminUser
        print("   ✅ AdminUser imported")

        from shared.models.telegram_channel import TelegramChannel
        print("   ✅ TelegramChannel imported")

        from shared.models.user_channel_membership import UserChannelMembership
        print("   ✅ UserChannelMembership imported")

        from shared.models.system_config import SystemConfig
        print("   ✅ SystemConfig imported")

        from shared.models.broadcast_message import BroadcastMessage
        print("   ✅ BroadcastMessage imported")

        from shared.models.system_log import SystemLog
        print("   ✅ SystemLog imported")

        print("3. Testing models package import...")
        from shared.models import User as User2
        print("   ✅ Models package imported")

        print("4. Testing database import...")
        from shared.database import Base as BaseFromDatabase
        print("   ✅ Base imported from database")

        print("5. Testing metadata...")
        print(f"   Tables in metadata: {list(Base.metadata.tables.keys())}")

        print("\n✅ All imports successful!")
        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)