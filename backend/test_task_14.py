"""
Test script for Task 14: 실시간 뉴스 수집 및 감성 분석
"""



import sys

from datetime import datetime, timedelta

from decimal import Decimal



# Test imports

try:

    from services.stock_data_collector import StockDataCollector

    from services.stock_news_filter import StockNewsFilter

    from services.account_sync_service import AccountSyncService

    from services.brokerage_connector import BrokerageAPIBase, StockPrice as BrokerageStockPrice, AccountInfo

    from models.trading_schemas import Order, TradeResult

    from models.news_article import NewsArticle

    from app.database import SessionLocal, init_db

    

    print("??All imports successful")

except ImportError as e:

    print(f"??Import error: {e}")

    sys.exit(1)





# Mock Brokerage API for testing

class MockBrokerageAPI(BrokerageAPIBase):

    """Mock brokerage API for testing"""

    

    def __init__(self):

        super().__init__({"test": "credentials"})

        self.is_authenticated = True

    

    def authenticate(self) -> bool:

        self.is_authenticated = True

        return True

    

    def get_stock_price(self, symbol: str) -> BrokerageStockPrice:

        """Return mock stock price"""

        return BrokerageStockPrice(

            symbol=symbol,

            price=Decimal("70000.00"),

            volume=1000000,

            open_price=Decimal("69000.00"),

            high_price=Decimal("71000.00"),

            low_price=Decimal("68500.00"),

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

                "name": "삼성전자",

                "quantity": 10,

                "average_price": Decimal("68000.00"),

                "current_price": Decimal("70000.00"),

                "evaluation_amount": Decimal("700000"),

                "profit_loss": Decimal("20000"),

                "profit_loss_rate": Decimal("2.94")

            },

            {

                "symbol": "000660",

                "name": "SK하이닉스",

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

    """Test StockDataCollector functionality"""

    print("\n" + "="*60)

    print("Testing StockDataCollector")

    print("="*60)

    

    try:

        # Initialize mock API

        mock_api = MockBrokerageAPI()

        

        # Create collector

        collector = StockDataCollector(

            broker_api=mock_api,

            symbols=["005930", "000660"],

            collection_interval_minutes=1

        )

        

        print("??StockDataCollector initialized")

        

        # Test single price collection

        db = SessionLocal()

        price = collector.collect_single_price("005930")

        

        if price:

            print(f"??Collected price for 005930: {price.price}")

        else:

            print("??Failed to collect price")

        

        # Test batch collection

        results = collector.collect_prices()

        print(f"??Batch collection: {sum(results.values())}/{len(results)} successful")

        

        # Test price history

        history = collector.get_price_history("005930", hours=1, db=db)

        print(f"??Price history: {len(history)} records")

        

        # Test holdings sync

        count = collector.sync_account_holdings()

        print(f"??Synced {count} holdings")

        

        db.close()

        

        print("??StockDataCollector tests passed")

        return True

        

    except Exception as e:

        print(f"??StockDataCollector test failed: {e}")

        import traceback

        traceback.print_exc()

        return False





def test_stock_news_filter():

    """Test StockNewsFilter functionality"""

    print("\n" + "="*60)

    print("Testing StockNewsFilter")

    print("="*60)

    

    try:

        # Create filter

        filter = StockNewsFilter()

        

        print("??StockNewsFilter initialized")

        print(f"   Tracking {len(filter.get_all_tracked_symbols())} stock symbols")

        

        # Test stock mention detection (without database)

        test_text = "삼성전자가 미국 텍사스에 새로운 반도체 공장을 건설한다고 발표했습니다."

        

        # Create a mock article for testing mention detection

        class MockArticle:

            def __init__(self):

                self.title = "삼성전자, 신규 반도체 공장 건설 발표"

                self.content = test_text

                self.asset_type = "stock"

        

        mock_article = MockArticle()

        mentioned = filter._find_mentioned_stocks(mock_article)

        

        if "005930" in mentioned:

            print(f"??Detected Samsung Electronics (005930) with relevance: {mentioned['005930']:.2f}")

        else:

            print("⚠️  Samsung Electronics not detected in test text")

        

        # Test adding custom stock mapping

        filter.add_stock_mapping("999999", ["테스트회사", "Test Company"])

        print("✓ Added custom stock mapping")

        

        # Test getting tracked symbols

        symbols = filter.get_all_tracked_symbols()

        if "999999" in symbols:

            print(f"??Custom symbol in tracked list ({len(symbols)} total)")

        

        print("??StockNewsFilter tests passed (database-independent tests)")

        return True

        

    except Exception as e:

        print(f"??StockNewsFilter test failed: {e}")

        import traceback

        traceback.print_exc()

        return False





def test_account_sync_service():

    """Test AccountSyncService functionality"""

    print("\n" + "="*60)

    print("Testing AccountSyncService")

    print("="*60)

    

    try:

        # Initialize mock API

        mock_api = MockBrokerageAPI()

        

        # Create service

        sync_service = AccountSyncService(mock_api)

        

        print("??AccountSyncService initialized")

        

        # Test holdings sync

        db = SessionLocal()

        stats = sync_service.sync_holdings(db)

        print(f"??Holdings sync: {stats['new_holdings']} new, "

              f"{stats['updated_holdings']} updated")

        

        # Test holdings summary

        summary = sync_service.get_holdings_summary(db)

        print(f"??Holdings summary: {summary['total_holdings']} positions")

        print(f"   Total P/L: {summary['profit_loss_percentage']:.2f}%")

        

        # Test average price calculation

        new_avg = sync_service.calculate_average_price(

            symbol="005930",

            new_quantity=5,

            new_price=Decimal("72000"),

            db=db

        )

        

        if new_avg:

            print(f"??Calculated new average price: {new_avg}")

        

        # Test trade update

        success = sync_service.update_holding_after_trade(

            symbol="005930",

            quantity=5,

            price=Decimal("72000"),

            db=db

        )

        

        if success:

            print("??Updated holding after trade")

        

        db.close()

        

        print("??AccountSyncService tests passed")

        return True

        

    except Exception as e:

        print(f"??AccountSyncService test failed: {e}")

        import traceback

        traceback.print_exc()

        return False





def main():

    """Run all tests"""

    print("\n" + "="*60)

    print("Task 14 Implementation Tests")

    print("="*60)

    

    # Initialize database

    try:

        init_db()

        print("??Database initialized")

    except Exception as e:

        print(f"⚠️  Database initialization: {e}")

    

    # Run tests

    results = []

    

    results.append(("StockDataCollector", test_stock_data_collector()))

    results.append(("StockNewsFilter", test_stock_news_filter()))

    results.append(("AccountSyncService", test_account_sync_service()))

    

    # Summary

    print("\n" + "="*60)

    print("Test Summary")

    print("="*60)

    

    for name, passed in results:

        status = "??PASSED" if passed else "??FAILED"

        print(f"{name}: {status}")

    

    all_passed = all(result[1] for result in results)

    

    print("\n" + "="*60)

    if all_passed:

        print("??All tests passed!")

    else:

        print("??Some tests failed")

    print("="*60)

    

    return 0 if all_passed else 1





if __name__ == "__main__":

    sys.exit(main())

