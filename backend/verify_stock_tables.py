"""
Verify that stock data tables were created correctly in the database
"""
import sqlite3
from pathlib import Path

def verify_tables():
    """Verify the stock data tables exist and have correct structure"""
    
    db_path = Path(__file__).parent.parent / "market_analyzer.db"
    
    if not db_path.exists():
        print(f"??Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("=" * 70)
        print("Database Table Verification")
        print("=" * 70)
        
        # Check stock_prices table
        print("\n1. Checking stock_prices table:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='stock_prices'")
        result = cursor.fetchone()
        if result:
            print("   ??Table exists")
            cursor.execute("PRAGMA table_info(stock_prices)")
            columns = cursor.fetchall()
            print(f"   ??Columns: {', '.join([col[1] for col in columns])}")
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='stock_prices'")
            indexes = cursor.fetchall()
            print(f"   ??Indexes: {len(indexes)} indexes created")
        else:
            print("   ??Table not found")
            return False
        
        # Check stock_news_relation table
        print("\n2. Checking stock_news_relation table:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='stock_news_relation'")
        result = cursor.fetchone()
        if result:
            print("   ??Table exists")
            cursor.execute("PRAGMA table_info(stock_news_relation)")
            columns = cursor.fetchall()
            print(f"   ??Columns: {', '.join([col[1] for col in columns])}")
            
            cursor.execute("PRAGMA foreign_key_list(stock_news_relation)")
            fks = cursor.fetchall()
            print(f"   ??Foreign keys: {len(fks)} foreign key(s) defined")
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='stock_news_relation'")
            indexes = cursor.fetchall()
            print(f"   ??Indexes: {len(indexes)} indexes created")
        else:
            print("   ??Table not found")
            return False
        
        # Check account_holdings table
        print("\n3. Checking account_holdings table:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='account_holdings'")
        result = cursor.fetchone()
        if result:
            print("   ??Table exists")
            cursor.execute("PRAGMA table_info(account_holdings)")
            columns = cursor.fetchall()
            print(f"   ??Columns: {', '.join([col[1] for col in columns])}")
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='account_holdings'")
            indexes = cursor.fetchall()
            print(f"   ??Indexes: {len(indexes)} indexes created")
        else:
            print("   ??Table not found")
            return False
        
        # Check alembic version
        print("\n4. Checking migration version:")
        cursor.execute("SELECT version_num FROM alembic_version")
        version = cursor.fetchone()
        if version:
            print(f"   ??Current version: {version[0]}")
        else:
            print("   ??No version recorded")
        
        # Test inserting sample data
        print("\n5. Testing data insertion:")
        try:
            # Insert a sample stock price
            cursor.execute("""
                INSERT INTO stock_prices (symbol, price, volume, timestamp)
                VALUES ('TEST', 100.50, 1000, datetime('now'))
            """)
            print("   ??Can insert into stock_prices")
            
            # Clean up
            cursor.execute("DELETE FROM stock_prices WHERE symbol='TEST'")
            
            # Insert a sample holding
            cursor.execute("""
                INSERT INTO account_holdings (symbol, quantity, average_price, updated_at)
                VALUES ('TEST', 10, 100.00, datetime('now'))
            """)
            print("   ??Can insert into account_holdings")
            
            # Clean up
            cursor.execute("DELETE FROM account_holdings WHERE symbol='TEST'")
            
            conn.commit()
        except Exception as e:
            print(f"   ??Insert test failed: {e}")
            return False
        
        print("\n" + "=" * 70)
        print("??All verification checks passed!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n??Verification error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    verify_tables()
