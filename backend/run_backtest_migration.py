"""
Run backtest tables migration
"""

import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic import command

def run_migration():
    """Run the backtest tables migration"""
    alembic_cfg = Config("alembic.ini")
    
    print("Running backtest tables migration...")
    try:
        command.upgrade(alembic_cfg, "007")
        print("??Backtest tables migration completed successfully")
    except Exception as e:
        print(f"??Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
