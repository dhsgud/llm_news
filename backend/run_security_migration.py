"""
Run security tables migration
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic import command
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the security tables migration"""
    try:
        # Create Alembic config
        alembic_cfg = Config("alembic.ini")
        
        logger.info("Running security tables migration (005)...")
        
        # Run upgrade to head
        command.upgrade(alembic_cfg, "005")
        
        logger.info("??Security tables migration completed successfully!")
        logger.info("Created tables:")
        logger.info("  - api_keys")
        logger.info("  - two_factor_secrets")
        logger.info("  - audit_logs")
        logger.info("  - trade_audit_logs")
        logger.info("  - encrypted_credentials")
        
        return True
        
    except Exception as e:
        logger.error(f"??Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
