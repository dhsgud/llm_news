"""
Standalone script to apply stock data tables migration
This script directly executes the SQL from migration 002
"""
import sys
from pathlib import Path
import sqlite3

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def apply_migration():
    """Apply the stock data tables migration"""
    
    # Connect to the database
    db_path = backend_dir.parent / "market_analyzer.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("Applying migration 002: Add stock data tables...")
        
        # Create stock_prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                volume BIGINT,
                open_price DECIMAL(10, 2),
                high_price DECIMAL(10, 2),
                low_price DECIMAL(10, 2),
                timestamp DATETIME NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_stock_prices_id ON stock_prices (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_stock_prices_symbol ON stock_prices (symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_stock_prices_timestamp ON stock_prices (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbol_timestamp ON stock_prices (symbol, timestamp)")
        print("??Created stock_prices table")
        
        # Create stock_news_relation table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_news_relation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_symbol VARCHAR(20) NOT NULL,
                article_id INTEGER NOT NULL,
                relevance_score FLOAT,
                FOREIGN KEY (article_id) REFERENCES news_articles (id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_stock_news_relation_id ON stock_news_relation (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_stock_news_relation_stock_symbol ON stock_news_relation (stock_symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_stock_news_relation_article_id ON stock_news_relation (article_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_article ON stock_news_relation (stock_symbol, article_id)")
        print("??Created stock_news_relation table")
        
        # Create account_holdings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL,
                quantity INTEGER NOT NULL,
                average_price DECIMAL(10, 2) NOT NULL,
                current_price DECIMAL(10, 2),
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_account_holdings_id ON account_holdings (id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_account_holdings_symbol ON account_holdings (symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holding_symbol ON account_holdings (symbol)")
        print("??Created account_holdings table")
        
        # Update alembic version table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL,
                CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
            )
        """)
        
        # Check current version
        cursor.execute("SELECT version_num FROM alembic_version")
        current_version = cursor.fetchone()
        
        if current_version is None:
            # No version yet, insert 002
            cursor.execute("INSERT INTO alembic_version (version_num) VALUES ('002')")
            print("??Set alembic version to 002")
        elif current_version[0] == '001':
            # Update from 001 to 002
            cursor.execute("UPDATE alembic_version SET version_num = '002'")
            print("??Updated alembic version from 001 to 002")
        else:
            print(f"??Alembic version is already at {current_version[0]}")
        
        conn.commit()
        print("\n??Migration completed successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('stock_prices', 'stock_news_relation', 'account_holdings')
            ORDER BY name
        """)
        tables = cursor.fetchall()
        print(f"\nVerified tables: {', '.join([t[0] for t in tables])}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n??Error applying migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    apply_migration()
