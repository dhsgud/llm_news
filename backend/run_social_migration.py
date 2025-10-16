"""
Run social sentiment migration
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic import command


def run_migration():
    """Run the social sentiment migration"""
    print("Running social sentiment migration...")
    
    # Create Alembic config
    alembic_cfg = Config("alembic.ini")
    
    # Run upgrade to head
    command.upgrade(alembic_cfg, "009")
    
    print("??Social sentiment migration completed successfully!")


if __name__ == "__main__":
    run_migration()
