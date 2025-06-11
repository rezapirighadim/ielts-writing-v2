"""
Simple database connection test script.
This script can be run to verify database connectivity.
"""

import sys
import os

# Add the parent directory to the path so we can import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import config, validate_environment
from shared.database import init_database, check_database_health, close_database

def test_database_connection():
    """Test database connection and display results."""
    print("🔧 IELTS Bot Database Connection Test")
    print("=" * 50)

    # Validate environment variables
    print("1. Checking environment variables...")
    if not validate_environment():
        print("❌ Environment validation failed!")
        return False

    print(f"   Database: {config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}")
    print(f"   User: {config.DB_USER}")
    print("   ✅ Environment variables OK")

    # Test database connection
    print("\n2. Testing database connection...")
    if not init_database():
        print("❌ Database connection failed!")
        return False

    print("   ✅ Database connection successful")

    # Check database health
    print("\n3. Checking database health...")
    health = check_database_health()

    print(f"   Status: {health.get('status', 'unknown')}")
    if 'database_version' in health:
        print(f"   Database Version: {health['database_version']}")
    if 'connection_pool_size' in health:
        print(f"   Pool Size: {health['connection_pool_size']}")
    if 'error' in health:
        print(f"   Error: {health['error']}")

    # Clean up
    close_database()

    if health.get('status') == 'healthy':
        print("\n🎉 Database test completed successfully!")
        return True
    else:
        print("\n❌ Database health check failed!")
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)