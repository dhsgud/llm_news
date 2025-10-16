"""
Script to apply auto trading tables migration
Run this to add TradeHistory and AutoTradeConfig tables to the database
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text

try:
    from app.database import engine, Base
    from models.trade_history import TradeHistory
    from models.auto_trade_config import AutoTradeConfig
except ImportError:
    from app.database import engine, Base
    from models.trade_history import TradeHistory
    from models.auto_trade_config import AutoTradeConfig

def run_migration():
    """Apply the auto trading tables migration"""
    print("Starting auto trading tables migration...")
    
    try:
        # Create tables
        print("Creating TradeHistory and AutoTradeConfig tables...")
        Base.metadata.create_all(bind=engine, tables=[
            TradeHistory.__table__,
            AutoTradeConfig.__table__
        ])
        
        # Verify tables were created
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('trade_history', 'auto_trade_config')"
            ))
            tables = [row[0] for row in result]
            
            if 'trade_history' in tables and 'auto_trade_config' in tables:
                print("??Tables created successfully:")
                print("  - trade_history")
                print("  - auto_trade_config")
                
                # Show table structure
                print("\nTradeHistory table structure:")
                result = conn.execute(text("PRAGMA table_info(trade_history)"))
                for row in result:
                    print(f"  {row[1]}: {row[2]}")
                
                print("\nAutoTradeConfig table structure:")
                result = conn.execute(text("PRAGMA table_info(auto_trade_config)"))
                for row in result:
                    print(f"  {row[1]}: {row[2]}")
                
                print("\n??Migration completed successfully!")
                return True
            else:
                print("??Error: Tables were not created")
                return False
                
    except Exception as e:
        print(f"??Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

