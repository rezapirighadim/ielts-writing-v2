"""
Debug script to diagnose import issues.
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def debug_imports():
    """Debug import issues step by step."""
    print("🔍 Debugging import issues...")
    print("=" * 50)

    # Check Python path
    print("1. Python path:")
    for i, path in enumerate(sys.path):
        print(f"   {i}: {path}")

    # Check if shared directory exists
    print("\n2. Checking shared directory structure:")
    shared_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'shared')
    print(f"   Shared path: {shared_path}")
    print(f"   Exists: {os.path.exists(shared_path)}")

    if os.path.exists(shared_path):
        print("   Contents:")
        for item in os.listdir(shared_path):
            item_path = os.path.join(shared_path, item)
            if os.path.isdir(item_path):
                print(f"   📁 {item}/")
            else:
                print(f"   📄 {item}")

    # Check models directory
    models_path = os.path.join(shared_path, 'models')
    print(f"\n3. Models directory: {models_path}")
    print(f"   Exists: {os.path.exists(models_path)}")

    if os.path.exists(models_path):
        print("   Contents:")
        for item in os.listdir(models_path):
            print(f"   📄 {item}")

    # Check __init__.py files
    print("\n4. Checking __init__.py files:")

    shared_init = os.path.join(shared_path, '__init__.py')
    print(f"   shared/__init__.py exists: {os.path.exists(shared_init)}")

    models_init = os.path.join(models_path, '__init__.py')
    print(f"   shared/models/__init__.py exists: {os.path.exists(models_init)}")

    if os.path.exists(models_init):
        print("   Content of shared/models/__init__.py:")
        with open(models_init, 'r') as f:
            content = f.read()
            print("   " + "\n   ".join(content.split('\n')[:20]))  # First 20 lines

    # Try imports step by step
    print("\n5. Testing imports step by step:")

    try:
        print("   Importing shared...")
        import shared
        print(f"   ✅ shared imported from: {shared.__file__}")
    except Exception as e:
        print(f"   ❌ Failed to import shared: {e}")
        return False

    try:
        print("   Importing shared.models...")
        import shared.models
        print(f"   ✅ shared.models imported from: {shared.models.__file__}")
        print(f"   shared.models.__all__: {getattr(shared.models, '__all__', 'Not defined')}")
        print(f"   shared.models dir: {[item for item in dir(shared.models) if not item.startswith('_')]}")
    except Exception as e:
        print(f"   ❌ Failed to import shared.models: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return False

    try:
        print("   Testing specific model import...")
        from shared.models import User
        print(f"   ✅ User imported: {User}")
    except Exception as e:
        print(f"   ❌ Failed to import User from shared.models: {e}")
        import traceback
        print(f"   Full traceback: {traceback.format_exc()}")
        return False

    print("\n✅ All debugging checks passed!")
    return True


if __name__ == "__main__":
    debug_imports()