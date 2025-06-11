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

def add_enhanced_submission_fields():
    """
    Add enhanced fields to submissions table for detailed analysis storage.
    """
    try:
        # Check if submissions table exists
        verification = verify_tables()
        if not verification['success'] or 'submissions' not in verification['existing_tables']:
            logger.error("❌ submissions table does not exist. Create tables first.")
            return False

        with db_manager.get_session() as session:
            logger.info("Adding enhanced fields to submissions table...")

            # List of enhanced fields to add
            enhanced_fields = [
                {
                    'name': 'character_count',
                    'sql': "ADD COLUMN character_count INT NULL AFTER word_count"
                },
                {
                    'name': 'validation_data',
                    'sql': "ADD COLUMN validation_data TEXT NULL AFTER feedback_text"
                },
                {
                    'name': 'analysis_metadata',
                    'sql': "ADD COLUMN analysis_metadata TEXT NULL AFTER validation_data"
                },
                {
                    'name': 'ai_analysis_data',
                    'sql': "ADD COLUMN ai_analysis_data TEXT NULL AFTER analysis_metadata"
                },
                {
                    'name': 'readability_score',
                    'sql': "ADD COLUMN readability_score DECIMAL(5,2) NULL AFTER ai_analysis_data"
                },
                {
                    'name': 'lexical_diversity',
                    'sql': "ADD COLUMN lexical_diversity DECIMAL(5,3) NULL AFTER readability_score"
                },
                {
                    'name': 'sentence_complexity_score',
                    'sql': "ADD COLUMN sentence_complexity_score DECIMAL(5,3) NULL AFTER lexical_diversity"
                },
                {
                    'name': 'structure_quality_score',
                    'sql': "ADD COLUMN structure_quality_score DECIMAL(5,3) NULL AFTER sentence_complexity_score"
                },
                {
                    'name': 'sentence_count',
                    'sql': "ADD COLUMN sentence_count INT NULL AFTER structure_quality_score"
                },
                {
                    'name': 'paragraph_count',
                    'sql': "ADD COLUMN paragraph_count INT NULL AFTER sentence_count"
                },
                {
                    'name': 'academic_words_count',
                    'sql': "ADD COLUMN academic_words_count INT NULL AFTER paragraph_count"
                },
                {
                    'name': 'transition_words_count',
                    'sql': "ADD COLUMN transition_words_count INT NULL AFTER academic_words_count"
                },
                {
                    'name': 'overall_quality',
                    'sql': "ADD COLUMN overall_quality ENUM('excellent', 'good', 'fair', 'needs_improvement', 'poor') NULL AFTER transition_words_count"
                },
                {
                    'name': 'recommendations_count',
                    'sql': "ADD COLUMN recommendations_count INT DEFAULT 0 AFTER overall_quality"
                },
                {
                    'name': 'validation_method',
                    'sql': "ADD COLUMN validation_method VARCHAR(50) DEFAULT 'enhanced' AFTER recommendations_count"
                },
                {
                    'name': 'confidence_score',
                    'sql': "ADD COLUMN confidence_score DECIMAL(5,3) NULL AFTER validation_method"
                },
                {
                    'name': 'created_at',
                    'sql': "ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP AFTER confidence_score"
                },
                {
                    'name': 'updated_at',
                    'sql': "ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER created_at"
                }
            ]

            # Check which fields already exist
            existing_columns = get_table_columns('submissions')
            fields_added = 0
            fields_skipped = 0

            for field in enhanced_fields:
                field_name = field['name']
                field_sql = field['sql']

                if field_name in existing_columns:
                    logger.info(f"   ⏭️ Field '{field_name}' already exists, skipping")
                    fields_skipped += 1
                else:
                    try:
                        session.execute(text(f"ALTER TABLE submissions {field_sql}"))
                        logger.info(f"   ✅ Added field: {field_name}")
                        fields_added += 1
                    except Exception as e:
                        logger.warning(f"   ⚠️ Could not add field '{field_name}': {e}")

            # Update status enum to include new values
            try:
                session.execute(text("""
                    ALTER TABLE submissions 
                    MODIFY COLUMN status ENUM('pending', 'processing', 'completed', 'failed', 'cancelled') 
                    DEFAULT 'pending'
                """))
                logger.info("   ✅ Updated status enum values")
            except Exception as e:
                logger.warning(f"   ⚠️ Could not update status enum: {e}")

            session.commit()

            logger.info(f"✅ Enhanced submission fields migration completed")
            logger.info(f"   📊 Fields added: {fields_added}")
            logger.info(f"   ⏭️ Fields skipped (already exist): {fields_skipped}")

            return True

    except Exception as e:
        logger.error(f"❌ Enhanced submission fields migration failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def get_table_columns(table_name):
    """
    Get list of column names for a given table.

    Args:
        table_name: Name of the table

    Returns:
        list: List of column names
    """
    try:
        with db_manager.get_session() as session:
            result = session.execute(text(f"DESCRIBE {table_name}"))
            columns = [row[0] for row in result.fetchall()]
            return columns
    except Exception as e:
        logger.error(f"❌ Failed to get columns for table {table_name}: {e}")
        return []

def verify_enhanced_fields():
    """
    Verify that enhanced submission fields were added correctly.

    Returns:
        dict: Verification results
    """
    try:
        expected_enhanced_fields = [
            'character_count', 'validation_data', 'analysis_metadata', 'ai_analysis_data',
            'readability_score', 'lexical_diversity', 'sentence_complexity_score',
            'structure_quality_score', 'sentence_count', 'paragraph_count',
            'academic_words_count', 'transition_words_count', 'overall_quality',
            'recommendations_count', 'validation_method', 'confidence_score',
            'created_at', 'updated_at'
        ]

        existing_columns = get_table_columns('submissions')

        verification_results = {}
        for field in expected_enhanced_fields:
            verification_results[field] = field in existing_columns

        all_fields_exist = all(verification_results.values())
        missing_fields = [field for field, exists in verification_results.items() if not exists]

        return {
            'success': True,
            'all_fields_exist': all_fields_exist,
            'fields': verification_results,
            'missing_fields': missing_fields,
            'existing_columns': existing_columns,
            'expected_fields': expected_enhanced_fields
        }

    except Exception as e:
        logger.error(f"❌ Enhanced fields verification failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'all_fields_exist': False,
            'fields': {},
            'missing_fields': [],
            'existing_columns': [],
            'expected_fields': []
        }

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

def run_complete_migration():
    """
    Run complete migration including enhanced fields.
    """
    logger.info("🚀 Starting complete database migration with enhanced features...")

    # Step 1: Run base migration
    logger.info("Running base migration...")
    if not run_migration():
        logger.error("❌ Base migration failed")
        return False

    # Step 2: Add enhanced submission fields
    logger.info("Adding enhanced submission fields...")
    if not add_enhanced_submission_fields():
        logger.error("❌ Enhanced fields migration failed")
        return False

    # Step 3: Verify enhanced fields
    logger.info("Verifying enhanced fields...")
    enhanced_verification = verify_enhanced_fields()
    if not enhanced_verification['success']:
        logger.error("❌ Enhanced fields verification failed")
        return False

    if not enhanced_verification['all_fields_exist']:
        logger.warning(f"⚠️ Some enhanced fields missing: {enhanced_verification['missing_fields']}")
        logger.warning("This may be expected if some fields already existed")

    logger.info("🎉 Complete database migration with enhanced features completed successfully!")
    logger.info("📊 Enhanced submission storage system is ready!")

    return True