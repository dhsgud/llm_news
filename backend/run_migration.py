"""
Script to run database migrations
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command

def run_migrations():
    """Run all pending migrations"""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("??Migrations completed successfully")

if __name__ == "__main__":
    run_migrations()
