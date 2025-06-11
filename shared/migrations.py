"""
Database migration utilities for creating and managing database schema.
"""

import logging
from sqlalchemy import text
from .database import db_manager, Base
from .config import config

logger = logging.getLogger(__name__)

def create_tables():
    """
    Create all database tables based on SQLAlchemy models.
    """
    try:
        if not db_manager._initialized:
            logger.error("Database not initialized. Call init_database() first.")
            return False

        logger.info("Importing models...")

        # Import models explicitly to register them with Base.metadata
        try:
            from .models.user import User
            from .models.submission import Submission
            from .models.admin_user import AdminUser
            from .models.telegram_channel import TelegramChannel
            from .models.user_channel_membership import UserChannelMembership
            from .models.system_config import SystemConfig
            from .models.broadcast_message import BroadcastMessage
            from .models.system_log import SystemLog

            logger.info("✅ All models imported successfully")

        except ImportError as e:
            logger.error(f"❌ Failed to import models: {e}")
            return False

        logger.info("Creating database tables...")

        # Create all tables
        Base.metadata.create_all(db_manager._engine)
        logger.info("✅ All database tables created successfully")

        # Verify tables were created
        verification = verify_tables()
        if verification['success'] and verification['all_tables_exist']:
            logger.info("✅ Table creation verified")
            return True
        else:
            logger.error("❌ Table verification failed after creation")
            logger.error(f"Verification result: {verification}")
            return False

    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def drop_tables():
    """
    Drop all database tables. Use with caution!
    """
    try:
        if not db_manager._initialized:
            logger.error("Database not initialized. Call init_database() first.")
            return False

        # Import all models first
        from .models.user import User
        from .models.submission import Submission
        from .models.admin_user import AdminUser
        from .models.telegram_channel import TelegramChannel
        from .models.user_channel_membership import UserChannelMembership
        from .models.system_config import SystemConfig
        from .models.broadcast_message import BroadcastMessage
        from .models.system_log import SystemLog

        # Drop all tables
        Base.metadata.drop_all(db_manager._engine)
        logger.info("⚠️ All database tables dropped")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to drop tables: {e}")
        return False

def insert_default_config():
    """Insert default system configuration values."""
    from .database import get_db_session
    from .models.system_config import SystemConfig, ConfigType

    default_configs = [
        {
            'config_key': 'free_monthly_limit',
            'config_value': str(config.FREE_MONTHLY_LIMIT),
            'description': 'Monthly submission limit for free users',
            'config_type': ConfigType.INT
        },
        {
            'config_key': 'premium_monthly_limit',
            'config_value': str(config.PREMIUM_MONTHLY_LIMIT),
            'description': 'Monthly submission limit for premium users',
            'config_type': ConfigType.INT
        },
        {
            'config_key': 'channel_bonus_requests',
            'config_value': str(config.CHANNEL_BONUS_REQUESTS),
            'description': 'Bonus requests per channel membership',
            'config_type': ConfigType.INT
        },
        {
            'config_key': 'max_bonus_requests',
            'config_value': str(config.MAX_BONUS_REQUESTS),
            'description': 'Maximum bonus requests a user can accumulate',
            'config_type': ConfigType.INT
        }
    ]

    try:
        # First verify that the system_config table exists
        verification = verify_tables()
        if not verification['success'] or 'system_config' not in verification['existing_tables']:
            logger.error("❌ system_config table does not exist. Create tables first.")
            return False

        with get_db_session() as session:
            inserted_count = 0

            for config_data in default_configs:
                # Check if config already exists
                existing = session.query(SystemConfig).filter_by(
                    config_key=config_data['config_key']
                ).first()

                if not existing:
                    new_config = SystemConfig(**config_data)
                    session.add(new_config)
                    inserted_count += 1
                    logger.info(f"✅ Added default config: {config_data['config_key']}")
                else:
                    logger.info(f"ℹ️ Config already exists: {config_data['config_key']}")

            logger.info(f"✅ Default configuration inserted successfully ({inserted_count} new configs)")
            return True

    except Exception as e:
        logger.error(f"❌ Failed to insert default config: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def verify_tables():
    """
    Verify that all expected tables exist in the database.
    """
    expected_tables = [
        'users',
        'submissions',
        'admin_users',
        'telegram_channels',
        'user_channel_memberships',
        'system_config',
        'broadcast_messages',
        'system_logs'
    ]

    try:
        with db_manager.get_session() as session:
            # Get list of existing tables
            result = session.execute(text("SHOW TABLES"))
            existing_tables = [row[0] for row in result.fetchall()]

            verification_results = {}
            for table in expected_tables:
                verification_results[table] = table in existing_tables

            all_tables_exist = all(verification_results.values())

            return {
                'success': True,
                'all_tables_exist': all_tables_exist,
                'tables': verification_results,
                'existing_tables': existing_tables,
                'expected_tables': expected_tables
            }

    except Exception as e:
        logger.error(f"❌ Table verification failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'all_tables_exist': False,
            'tables': {},
            'existing_tables': [],
            'expected_tables': expected_tables
        }

def check_existing_tables():
    """Check what tables currently exist in the database."""
    try:
        with db_manager.get_session() as session:
            result = session.execute(text("SHOW TABLES"))
            existing_tables = [row[0] for row in result.fetchall()]

            logger.info(f"Existing tables in database: {existing_tables}")
            return existing_tables

    except Exception as e:
        logger.error(f"❌ Failed to check existing tables: {e}")
        return []

def run_migration():
    """
    Run complete database migration: create tables and insert default data.
    """
    logger.info("🚀 Starting database migration...")

    # Step 1: Check existing tables
    logger.info("Checking existing tables...")
    existing_tables = check_existing_tables()

    # Step 2: Create tables
    logger.info("Creating database tables...")
    if not create_tables():
        logger.error("❌ Migration failed: Could not create tables")
        return False

    # Step 3: Verify tables were created
    logger.info("Verifying table creation...")
    verification = verify_tables()
    if not verification['success']:
        logger.error("❌ Migration failed: Could not verify tables")
        return False

    if not verification['all_tables_exist']:
        logger.error("❌ Migration failed: Not all tables were created")
        logger.error(f"Missing tables: {[t for t, exists in verification['tables'].items() if not exists]}")
        return False

    # Step 4: Insert default configuration (only after tables are confirmed to exist)
    logger.info("Inserting default configuration...")
    if not insert_default_config():
        logger.error("❌ Migration failed: Could not insert default config")
        return False

    logger.info("🎉 Database migration completed successfully!")
    return True