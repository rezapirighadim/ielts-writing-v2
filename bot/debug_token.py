"""
Debug script to check bot token format without exposing the actual token.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.config import config


def debug_token():
    """Debug bot token format."""
    print("🔍 Debugging Bot Token Format")
    print("=" * 50)

    token = config.TELEGRAM_BOT_TOKEN

    if not token:
        print("❌ No bot token found in environment variables")
        print("Make sure TELEGRAM_BOT_TOKEN is set in your .env file")
        return False

    print(f"Token length: {len(token)}")
    print(f"Starts with 'bot': {token.startswith('bot')}")
    print(f"Contains colon: {':' in token}")

    if ':' in token:
        # Check format without exposing the token
        work_token = token
        if work_token.startswith('bot'):
            work_token = work_token[3:]

        parts = work_token.split(':')
        if len(parts) == 2:
            bot_id_part, token_part = parts
            print(f"Bot ID part length: {len(bot_id_part)}")
            print(f"Bot ID is numeric: {bot_id_part.isdigit()}")
            print(f"Token part length: {len(token_part)}")

            # Check first few characters without exposing full token
            print(f"Token starts with: {token[:10]}...")
            print(f"Token format appears correct: {len(token_part) >= 30}")
        else:
            print("❌ Token doesn't have exactly one colon")
    else:
        print("❌ Token doesn't contain a colon")

    print("\nIf your token is from @BotFather, it should look like:")
    print("123456789:ABCDEF1234567890abcdef1234567890ABCDEF12")
    print("or")
    print("bot123456789:ABCDEF1234567890abcdef1234567890ABCDEF12")

    return True


if __name__ == "__main__":
    debug_token()