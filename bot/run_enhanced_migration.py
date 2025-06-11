#!/usr/bin/env python3
"""
Run enhanced submission storage migration.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from shared.migrations import add_enhanced_submission_fields, verify_enhanced_fields, run_complete_migration
from shared.database import init_database, close_database
from shared.config import validate_environment
from config.logging_config import setup_logging
import logging

# Set up logging
setup_logging()
logger = logging.getLogger(__name__)


def main():
    """Run the enhanced submission migration."""
    print("🚀 Enhanced Submission Storage Migration")
    print("=" * 50)

    # Validate environment
    print("1. Validating environment...")
    if not validate_environment():
        print("❌ Environment validation failed")
        sys.exit(1)
    print("   ✅ Environment validated")

    # Initialize database
    print("\n2. Initializing database connection...")
    if not init_database():
        print("❌ Database initialization failed")
        sys.exit(1)
    print("   ✅ Database connected")

    try:
        # Option 1: Run only enhanced fields migration (if base tables exist)
        print("\n3. Checking if this is an upgrade or fresh install...")
        verification = verify_enhanced_fields()

        if verification['success'] and verification['all_fields_exist']:
            print("✅ Enhanced fields already exist!")
            print("   📊 All 18 enhanced fields are present")
            print("   🎯 Enhanced storage system is ready!")
            return

        # Option 2: Run enhanced fields migration
        print("\n🔄 Running enhanced submission fields migration...")
        success = add_enhanced_submission_fields()

        if success:
            print("✅ Enhanced submission migration completed successfully!")

            # Verify the migration
            print("\n4. Verifying enhanced fields...")
            verification = verify_enhanced_fields()

            if verification['success']:
                print(f"   ✅ {len([f for f in verification['fields'].values() if f])} enhanced fields verified")

                if verification['missing_fields']:
                    print(f"   ⚠️ Missing fields: {verification['missing_fields']}")
                else:
                    print("   🎯 All enhanced fields present!")

            print("\n📋 Enhanced fields added to submissions table:")
            enhanced_fields_info = [
                ("character_count", "Text character count"),
                ("validation_data", "JSON validation results"),
                ("analysis_metadata", "JSON analysis metadata"),
                ("ai_analysis_data", "JSON AI evaluation data"),
                ("readability_score", "Text readability metric"),
                ("lexical_diversity", "Vocabulary variety score"),
                ("sentence_complexity_score", "Sentence structure complexity"),
                ("structure_quality_score", "Text organization quality"),
                ("sentence_count", "Number of sentences"),
                ("paragraph_count", "Number of paragraphs"),
                ("academic_words_count", "Academic vocabulary usage"),
                ("transition_words_count", "Transition words usage"),
                ("overall_quality", "Quality classification"),
                ("recommendations_count", "Number of improvement suggestions"),
                ("validation_method", "Validation approach used"),
                ("confidence_score", "Validation confidence level"),
                ("created_at", "Record creation timestamp"),
                ("updated_at", "Record update timestamp")
            ]

            for field_name, description in enhanced_fields_info:
                status = "✅" if field_name in verification.get('existing_columns', []) else "❌"
                print(f"   {status} {field_name} - {description}")

            print("\n🎯 Enhanced storage system ready for use!")
            print("   📊 Detailed validation and analysis data storage")
            print("   🤖 AI evaluation results integration")
            print("   📈 User progress tracking and analytics")

        else:
            print("❌ Enhanced submission migration failed!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Migration error: {e}")
        logger.error(f"Enhanced migration failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        sys.exit(1)

    finally:
        # Close database connections
        close_database()
        print("\n🔚 Database connections closed")


if __name__ == "__main__":
    main()