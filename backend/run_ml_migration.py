"""
Run ML Learning Tables Migration
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic import command
from alembic.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the ML learning tables migration"""
    try:
        # Create Alembic config
        alembic_cfg = Config("alembic.ini")
        
        logger.info("Running ML learning tables migration (006)...")
        
        # Run upgrade to head
        command.upgrade(alembic_cfg, "head")
        
        logger.info("??ML learning tables migration completed successfully")
        logger.info("Tables created:")
        logger.info("  - trade_patterns")
        logger.info("  - learned_strategies")
        logger.info("  - learning_sessions")
        
        return True
        
    except Exception as e:
        logger.error(f"??Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
