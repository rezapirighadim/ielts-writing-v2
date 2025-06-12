#!/usr/bin/env python3
"""
Minimal OpenAI test to debug the proxies issue.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Test 0: Check .env file loading
print("🔍 Debug Step 0: .env File Check")
try:
    from dotenv import load_dotenv

    # Check current directory
    current_dir = os.getcwd()
    print(f"   📁 Current directory: {current_dir}")

    # Check for .env in current directory
    env_file = os.path.join(current_dir, '.env')
    print(f"   📄 Looking for .env at: {env_file}")

    if os.path.exists(env_file):
        print("   ✅ .env file found!")

        # Load .env manually
        load_dotenv(env_file)
        print("   ✅ .env loaded manually")

        # Check if API key is now available
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print(f"   ✅ API key loaded: {api_key[:8]}...")
        else:
            print("   ❌ API key still not found after loading .env")

            # Show what's in .env file
            print("   📄 .env file contents:")
            with open(env_file, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    if 'OPENAI_API_KEY' in line:
                        print(f"   {i}: {line.strip()}")
    else:
        print("   ❌ .env file not found!")

        # Check parent directory
        parent_env = os.path.join(os.path.dirname(current_dir), '.env')
        print(f"   📄 Checking parent directory: {parent_env}")

        if os.path.exists(parent_env):
            print("   ✅ .env found in parent directory!")
            load_dotenv(parent_env)
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                print(f"   ✅ API key loaded from parent: {api_key[:8]}...")
            else:
                print("   ❌ API key not found in parent .env")
        else:
            print("   ❌ .env not found in parent directory either!")

except Exception as e:
    print(f"   ❌ .env loading failed: {e}")

# Test 1: Check OpenAI version
print("\n🔍 Debug Step 1: OpenAI Version Check")
try:
    import openai

    print(f"   ✅ OpenAI version: {openai.__version__}")
except ImportError as e:
    print(f"   ❌ OpenAI import failed: {e}")
    sys.exit(1)

# Test 2: Direct OpenAI client creation
print("\n🔍 Debug Step 2: Direct OpenAI Client Test")
try:
    from openai import OpenAI

    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("   ❌ OPENAI_API_KEY not found in environment")
        print("   💡 Please check your .env file location and content")
        sys.exit(1)

    print(f"   ✅ API key found: {api_key[:8]}...")

    # Try creating client with minimal parameters
    print("   🔧 Creating OpenAI client...")

    # Try different initialization approaches for compatibility
    try:
        # Method 1: Most minimal initialization
        client = OpenAI(api_key=api_key)
        print("   ✅ OpenAI client created successfully!")
    except TypeError as e:
        if 'proxies' in str(e):
            print(f"   ⚠️ Method 1 failed (proxies issue): {e}")
            print("   🔧 Trying with custom http client...")

            # Method 2: Try with custom http client to bypass proxies issue
            try:
                import httpx

                # Create httpx client without problematic parameters
                http_client = httpx.Client(
                    timeout=60.0,
                    follow_redirects=True
                )

                client = OpenAI(
                    api_key=api_key,
                    http_client=http_client
                )
                print("   ✅ OpenAI client created with custom http client!")
            except Exception as e2:
                print(f"   ❌ Method 2 also failed: {e2}")
                print("   💡 Try: pip install 'httpx==0.27.0'")
                raise e
        else:
            raise e

    # Test a simple API call
    print("   🔧 Testing API call...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print("   ✅ API call successful!")
    print(f"   📝 Response: {response.choices[0].message.content}")

except Exception as e:
    print(f"   ❌ Direct OpenAI test failed: {e}")
    print(f"   🔍 Error type: {type(e)}")
    import traceback

    traceback.print_exc()

# Test 3: Check environment variables
print("\n🔍 Debug Step 3: Environment Variables")
env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'http_proxy', 'https_proxy']
for var in env_vars:
    value = os.getenv(var)
    if value:
        print(f"   ⚠️ {var}: {value}")
    else:
        print(f"   ✅ {var}: Not set")

# Test 4: Check our config
print("\n🔍 Debug Step 4: Our Config Test")
try:
    from shared.config import config

    print(f"   ✅ Config loaded")
    print(f"   🔧 OPENAI_API_KEY: {config.OPENAI_API_KEY[:8] if config.OPENAI_API_KEY else 'NOT SET'}...")
    print(f"   🔧 OPENAI_MODEL: {config.OPENAI_MODEL}")
    print(f"   🔧 OPENAI_MAX_RETRIES: {config.OPENAI_MAX_RETRIES}")
except Exception as e:
    print(f"   ❌ Config test failed: {e}")

print("\n🎯 Debugging complete!")