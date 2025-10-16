"""
Run multi-asset migration
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from alembic.config import Config
from alembic import command

def run_migration():
    """Run the multi-asset migration"""
    alembic_cfg = Config("alembic.ini")
    
    print("Running multi-asset migration (008)...")
    try:
        command.upgrade(alembic_cfg, "008")
        print("??Multi-asset migration completed successfully")
    except Exception as e:
        print(f"??Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
