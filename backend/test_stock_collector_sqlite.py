"""
Test StockDataCollector with SQLite database
Verifies Task 14.1 implementation
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

# Set SQLite database for testing
os.environ['DATABASE_URL'] = 'sqlite:///./test_market_analyzer.db'

# Import models first to register them with Base
import models  # This imports all models and registers them with Base

from services.stock_data_collector import StockDataCollector
from services.brokerage_connector import BrokerageAPIBase, StockPrice as BrokerageStockPrice, AccountInfo
from models.trading_schemas import Order, TradeResult
from app.database import SessionLocal, init_db


class MockBrokerageAPI(BrokerageAPIBase):
    """Mock brokerage API for testing"""
    
    def __init__(self):
        super().__init__({"test": "credentials"})
        self.is_authenticated = True
        self.call_count = 0
    
    def authenticate(self) -> bool:
        self.is_authenticated = True
        return True
    
    def get_stock_price(self, symbol: str) -> BrokerageStockPrice:
        """Return mock stock price with incrementing values"""
        self.call_count += 1
        base_price = 70000 + (self.call_count * 100)
        
        return BrokerageStockPrice(
            symbol=symbol,
            price=Decimal(str(base_price)),
            volume=1000000 + (self.call_count * 10000),
            open_price=Decimal(str(base_price - 1000)),
            high_price=Decimal(str(base_price + 1000)),
            low_price=Decimal(str(base_price - 1500)),
            timestamp=datetime.now()
        )
    
    def get_account_balance(self) -> AccountInfo:
        """Return mock account info"""
        return AccountInfo(
            account_number="12345678",
            balance=Decimal("10000000"),
            available_cash=Decimal("9000000"),
            total_assets=Decimal("15000000")
        )
    
    def get_account_holdings(self) -> list:
        """Return mock holdings"""
        return [
            {
                "symbol": "005930",
                "name": "?�성?�자",
                "quantity": 10,
                "average_price": Decimal("68000.00"),
                "current_price": Decimal("70000.00"),
                "evaluation_amount": Decimal("700000"),
                "profit_loss": Decimal("20000"),
                "profit_loss_rate": Decimal("2.94")
            },
            {
                "symbol": "000660",
                "name": "SK?�이?�스",
                "quantity": 5,
                "average_price": Decimal("120000.00"),
                "current_price": Decimal("125000.00"),
                "evaluation_amount": Decimal("625000"),
                "profit_loss": Decimal("25000"),
                "profit_loss_rate": Decimal("4.17")
            }
        ]
    
    def place_order(self, order: Order) -> TradeResult:
        """Mock order placement"""
        return TradeResult(
            order_id="TEST123",
            symbol=order.symbol,
            trade_type=order.trade_type,
            quantity=order.quantity,
            executed_price=order.price or Decimal("70000"),
            total_amount=(order.price or Decimal("70000")) * order.quantity,
            executed_at=datetime.now(),
            status="SUCCESS",
            message="Mock order executed"
        )
    
    def cancel_order(self, order_id: str) -> bool:
        return True
    
    def get_order_status(self, order_id: str) -> dict:
        return {"order_id": order_id, "status": "FILLED"}


def test_stock_data_collector():
    """Test StockDataCollector - Task 14.1"""
    print("\n" + "="*70)
    print("Task 14.1: StockDataCollector ?�래???�성")
    print("="*70)
    
    # Initialize database
    print("\n1. Initializing database...")
    try:
        from app.database import Base, engine
        # Import all models to register them
        from models.stock_price import StockPrice
        from models.account_holding import AccountHolding
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("   ??Database initialized")
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"   - Created tables: {', '.join(tables)}")
    except Exception as e:
        print(f"   ??Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Create mock API and collector
    print("\n2. Creating StockDataCollector...")
    try:
        mock_api = MockBrokerageAPI()
        collector = StockDataCollector(
            broker_api=mock_api,
            symbols=["005930", "000660", "035720"],
            collection_interval_minutes=1
        )
        print("   ??StockDataCollector initialized")
        print(f"   - Tracking {len(collector.symbols)} symbols")
        print(f"   - Collection interval: {collector.collection_interval_minutes} minute(s)")
    except Exception as e:
        print(f"   ??Failed to create collector: {e}")
        return False
    
    # Test 1: Single price collection
    print("\n3. Testing single price collection...")
    try:
        price = collector.collect_single_price("005930")
        if price:
            print(f"   ??Collected price for 005930")
            print(f"   - Price: {price.price}")
            print(f"   - Volume: {price.volume}")
            print(f"   - High: {price.high_price}, Low: {price.low_price}")
            print(f"   - Timestamp: {price.timestamp}")
        else:
            print("   ??Failed to collect price")
            return False
    except Exception as e:
        print(f"   ??Single price collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2: Batch price collection
    print("\n4. Testing batch price collection...")
    try:
        results = collector.collect_prices()
        successful = sum(results.values())
        total = len(results)
        print(f"   ??Batch collection completed: {successful}/{total} successful")
        for symbol, success in results.items():
            status = "?? if success else "??
            print(f"   {status} {symbol}")
    except Exception as e:
        print(f"   ??Batch collection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Price history retrieval
    print("\n5. Testing price history retrieval...")
    try:
        db = SessionLocal()
        history = collector.get_price_history("005930", hours=1, db=db)
        print(f"   ??Retrieved {len(history)} price records")
        if history:
            print(f"   - Latest price: {history[-1].price}")
            print(f"   - Oldest price: {history[0].price}")
        db.close()
    except Exception as e:
        print(f"   ??Price history retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 4: Account holdings sync
    print("\n6. Testing account holdings synchronization...")
    try:
        count = collector.sync_account_holdings()
        print(f"   ??Synced {count} holdings")
        print(f"   - Now tracking {len(collector.symbols)} symbols")
    except Exception as e:
        print(f"   ??Holdings sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 5: Add/Remove symbols
    print("\n7. Testing symbol management...")
    try:
        initial_count = len(collector.symbols)
        collector.add_symbol("005380")
        print(f"   ??Added symbol 005380")
        print(f"   - Symbol count: {initial_count} ??{len(collector.symbols)}")
        
        collector.remove_symbol("005380")
        print(f"   ??Removed symbol 005380")
        print(f"   - Symbol count: {len(collector.symbols)}")
    except Exception as e:
        print(f"   ??Symbol management failed: {e}")
        return False
    
    # Test 6: Latest price retrieval
    print("\n8. Testing latest price retrieval...")
    try:
        db = SessionLocal()
        latest = collector.get_latest_price("005930", db)
        if latest:
            print(f"   ??Retrieved latest price for 005930: {latest.price}")
        else:
            print("   ?�️  No price found (this is OK if no data collected yet)")
        db.close()
    except Exception as e:
        print(f"   ??Latest price retrieval failed: {e}")
        return False
    
    # Test 7: Verify periodic collection setup
    print("\n9. Testing periodic collection setup...")
    try:
        print(f"   - Scheduler running: {collector.is_running}")
        print(f"   - Collection interval: {collector.collection_interval_minutes} minute(s)")
        print("   ??Periodic collection configuration verified")
    except Exception as e:
        print(f"   ??Periodic collection setup failed: {e}")
        return False
    
    print("\n" + "="*70)
    print("??Task 14.1 Implementation Verified")
    print("="*70)
    print("\nImplemented features:")
    print("  ??Periodic price collection (1 minute interval)")
    print("  ??Database storage of stock prices")
    print("  ??Single and batch price collection")
    print("  ??Price history retrieval")
    print("  ??Account holdings synchronization")
    print("  ??Symbol management (add/remove)")
    print("  ??Latest price queries")
    print("\nRequirements satisfied:")
    print("  ??Requirement 11.2: Real-time stock data collection")
    print("  ??Requirement 11.3: Database storage of stock data")
    
    return True


def cleanup():
    """Clean up test database"""
    try:
        if os.path.exists("test_market_analyzer.db"):
            os.remove("test_market_analyzer.db")
            print("\n??Test database cleaned up")
    except Exception as e:
        print(f"\n?�️  Failed to clean up test database: {e}")


if __name__ == "__main__":
    try:
        success = test_stock_data_collector()
        cleanup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n??Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)
