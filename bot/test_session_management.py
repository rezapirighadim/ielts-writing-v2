"""
Test script for session management functionality.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.logging_config import setup_logging
from session.session_manager import SessionManager, UserSession
from session.conversation_state import ConversationState, ConversationStep


async def test_session_management():
    """Test session management functionality."""

    # Set up logging
    setup_logging()

    print("🧪 Testing Session Management")
    print("=" * 50)

    # Test 1: Create session manager
    print("1. Testing SessionManager creation...")
    try:
        session_manager = SessionManager()
        print("   ✅ SessionManager created")
    except Exception as e:
        print(f"   ❌ SessionManager creation failed: {e}")
        return False

    # Test 2: Create user session
    print("2. Testing UserSession creation...")
    try:
        test_telegram_id = 123456789
        test_user_id = 1

        session = session_manager.get_session(
            telegram_id=test_telegram_id,
            user_id=test_user_id,
            username="testuser"
        )

        if session:
            print(f"   ✅ Session created: {session.telegram_id}")
            print(f"   📊 Initial step: {session.conversation_state.current_step.value}")
        else:
            print("   ❌ Session creation failed")
            return False
    except Exception as e:
        print(f"   ❌ Session creation failed: {e}")
        return False

    # Test 3: Conversation state management
    print("3. Testing conversation state...")
    try:
        # Set conversation step
        success = session_manager.set_conversation_step(
            telegram_id=test_telegram_id,
            step=ConversationStep.SUBMIT_TASK_SELECTION,
            data={'task_info': 'IELTS Writing Task'}
        )

        if success:
            print("   ✅ Conversation step set")

            # Get conversation state
            conv_state = session_manager.get_conversation_state(test_telegram_id)
            if conv_state:
                print(f"   📈 Current step: {conv_state.current_step.value}")
                print(f"   💾 Data: {conv_state.data}")
                print(f"   🔄 Flow type: {conv_state.get_flow_type()}")
            else:
                print("   ❌ Could not retrieve conversation state")
                return False
        else:
            print("   ❌ Could not set conversation step")
            return False
    except Exception as e:
        print(f"   ❌ Conversation state test failed: {e}")
        return False

    # Test 4: Session activity tracking
    print("4. Testing session activity...")
    try:
        session_manager.update_session_activity(
            telegram_id=test_telegram_id,
            message_id=12345,
            command="/submit"
        )

        session = session_manager.get_session(test_telegram_id)
        if session:
            print(f"   ✅ Activity updated")
            print(f"   📨 Last message ID: {session.last_message_id}")
            print(f"   ⌨️ Last command: {session.last_command}")
            print(f"   📊 Message count: {session.message_count}")
        else:
            print("   ❌ Could not retrieve session")
            return False
    except Exception as e:
        print(f"   ❌ Activity tracking test failed: {e}")
        return False

    # Test 5: Multiple sessions
    print("5. Testing multiple sessions...")
    try:
        # Create second session
        test_telegram_id_2 = 987654321
        session2 = session_manager.get_session(
            telegram_id=test_telegram_id_2,
            user_id=2,
            username="testuser2"
        )

        # Set different conversation steps
        session_manager.set_conversation_step(
            telegram_id=test_telegram_id_2,
            step=ConversationStep.CHANNEL_CHECKING
        )

        # Get active sessions
        active_sessions = session_manager.get_active_sessions()
        print(f"   ✅ Active sessions: {len(active_sessions)}")

        # Get sessions by flow
        submission_sessions = session_manager.get_sessions_by_flow("submission")
        channel_sessions = session_manager.get_sessions_by_flow("channel")

        print(f"   📝 Submission flow sessions: {len(submission_sessions)}")
        print(f"   📢 Channel flow sessions: {len(channel_sessions)}")

    except Exception as e:
        print(f"   ❌ Multiple sessions test failed: {e}")
        return False

    # Test 6: Session statistics
    print("6. Testing session statistics...")
    try:
        stats = session_manager.get_session_statistics()
        print(f"   ✅ Session statistics retrieved")
        print(f"   📊 Total sessions: {stats['total_active_sessions']}")
        print(f"   🔄 Flow distribution: {stats['flow_distribution']}")
        print(f"   📈 Step distribution: {stats['step_distribution']}")

    except Exception as e:
        print(f"   ❌ Statistics test failed: {e}")
        return False

    # Test 7: Conversation reset
    print("7. Testing conversation reset...")
    try:
        # Reset first session
        reset_success = session_manager.reset_conversation(test_telegram_id)
        if reset_success:
            conv_state = session_manager.get_conversation_state(test_telegram_id)
            if conv_state and conv_state.current_step == ConversationStep.IDLE:
                print("   ✅ Conversation reset to idle")
            else:
                print("   ❌ Conversation not properly reset")
                return False
        else:
            print("   ❌ Reset failed")
            return False
    except Exception as e:
        print(f"   ❌ Reset test failed: {e}")
        return False

    # Test 8: Expiration handling
    print("8. Testing expiration handling...")
    try:
        # Create a conversation state and manually expire it
        conv_state = session_manager.get_conversation_state(test_telegram_id)
        if conv_state:
            # Set expiration to past
            conv_state.expires_at = datetime.utcnow() - timedelta(minutes=1)

            # Check if expired
            if conv_state.is_expired():
                print("   ✅ Expiration detection works")

                # Test cleanup
                cleaned = session_manager.cleanup_expired_sessions()
                print(f"   🧹 Cleaned up sessions: {cleaned}")
            else:
                print("   ❌ Expiration detection failed")
                return False
        else:
            print("   ❌ Could not get conversation state for expiration test")
            return False
    except Exception as e:
        print(f"   ❌ Expiration test failed: {e}")
        return False

    print("\n🎉 All session management tests passed!")
    print("\nNext steps:")
    print("1. Session management is ready for use in handlers")
    print("2. Conversation flow tracking operational")
    print("3. Multi-step interactions supported")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_session_management())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Test cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)