"""
Database migration script for IELTS Telegram Bot.
Run this script to create database tables and insert default data.
"""

import sys
import os
import logging

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging to see detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from shared.config import validate_environment
from shared.database import init_database, close_database
from shared.migrations import run_migration, verify_tables, check_existing_tables

def main():
    """Main migration function."""
    print("🗄️ IELTS Bot Database Migration")
    print("=" * 50)

    # Step 1: Validate environment
    print("1. Validating environment...")
    if not validate_environment():
        print("❌ Environment validation failed!")
        return False

    print("   ✅ Environment OK")

    # Step 2: Initialize database connection
    print("2. Connecting to database...")
    if not init_database():
        print("❌ Database connection failed!")
        return False

    print("   ✅ Database connected")

    # Step 3: Check what currently exists
    print("3. Checking existing database state...")
    existing_tables = check_existing_tables()
    if existing_tables:
        print(f"   Found existing tables: {existing_tables}")
    else:
        print("   No existing tables found (fresh database)")

    # Step 4: Run migration
    print("4. Running migration...")
    if not run_migration():
        print("❌ Migration failed!")
        close_database()
        return False

    print("   ✅ Migration completed")

    # Step 5: Final verification
    print("5. Final verification...")
    verification = verify_tables()

    if verification['success'] and verification['all_tables_exist']:
        print("   ✅ All tables verified")
        print("\n📊 Created tables:")
        for table, exists in verification['tables'].items():
            status = "✅" if exists else "❌"
            print(f"   {status} {table}")
    else:
        print("   ❌ Table verification failed")
        if 'error' in verification:
            print(f"   Error: {verification['error']}")

        # Show what's missing
        if verification.get('tables'):
            missing = [t for t, exists in verification['tables'].items() if not exists]
            if missing:
                print(f"   Missing tables: {missing}")

        close_database()
        return False

    # Cleanup
    close_database()

    print("\n🎉 Database migration completed successfully!")
    print("\nNext steps:")
    print("1. You can now test the bot connection")
    print("2. Run database_test.py to verify connectivity")
    print("3. Proceed to the next development step")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)