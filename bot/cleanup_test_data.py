"""
Cleanup test data from database.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.database import init_database, get_db_session, close_database
from shared.models.telegram_channel import TelegramChannel
from shared.models.user import User


def cleanup_test_data():
    """Clean up test data from database."""
    print("🧹 Cleaning up test data...")

    if not init_database():
        print("❌ Database connection failed!")
        return False

    try:
        with get_db_session() as session:
            # Remove test channel
            test_channels = session.query(TelegramChannel).filter(
                TelegramChannel.channel_username.like('testchannel%')
            ).all()

            for channel in test_channels:
                session.delete(channel)
                print(f"   🗑️ Removed test channel: @{channel.channel_username}")

            # Remove test users
            test_users = session.query(User).filter(
                User.telegram_id.in_([999888777, 555666777, 123456789])
            ).all()

            for user in test_users:
                session.delete(user)
                print(f"   🗑️ Removed test user: {user.display_name}")

            print("✅ Test data cleanup completed")

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False
    finally:
        close_database()

    return True


if __name__ == "__main__":
    cleanup_test_data()