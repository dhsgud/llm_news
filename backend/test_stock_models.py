"""
Test script to verify stock data models can be imported and used
"""
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_imports():
    """Test that all new models can be imported"""
    print("Testing model imports...")
    
    try:
        from models import (
            StockPrice, StockPriceCreate, StockPriceResponse,
            StockNewsRelation, StockNewsRelationCreate, StockNewsRelationResponse,
            AccountHolding, AccountHoldingCreate, AccountHoldingResponse,
            Order, TradeResult, OrderRequest, OrderResponse
        )
        print("??All models imported successfully")
        return True
    except ImportError as e:
        print(f"??Import error: {e}")
        return False

def test_pydantic_schemas():
    """Test that Pydantic schemas work correctly"""
    print("\nTesting Pydantic schemas...")
    
    from models import (
        StockPriceCreate,
        Order,
        TradeResult
    )
    
    try:
        # Test StockPriceCreate
        stock_price = StockPriceCreate(
            symbol="005930",
            price=Decimal("75000.00"),
            volume=1000000,
            open_price=Decimal("74500.00"),
            high_price=Decimal("75500.00"),
            low_price=Decimal("74000.00"),
            timestamp=datetime.now()
        )
        print(f"??StockPriceCreate: {stock_price.symbol} @ {stock_price.price}")
        
        # Test Order
        order = Order(
            symbol="005930",
            trade_type="BUY",
            quantity=10,
            price=Decimal("75000.00"),
            order_type="LIMIT"
        )
        print(f"??Order: {order.trade_type} {order.quantity} shares of {order.symbol}")
        
        # Test TradeResult
        trade_result = TradeResult(
            order_id="ORD001",
            symbol="005930",
            trade_type="BUY",
            quantity=10,
            executed_price=Decimal("74500.00"),
            total_amount=Decimal("745000.00"),
            executed_at=datetime.now(),
            status="SUCCESS"
        )
        print(f"??TradeResult: {trade_result.status} - {trade_result.quantity} @ {trade_result.executed_price}")
        
        return True
    except Exception as e:
        print(f"??Schema validation error: {e}")
        return False

def test_database_models():
    """Test that database models are properly defined"""
    print("\nTesting database models...")
    
    from models import StockPrice, StockNewsRelation, AccountHolding
    
    try:
        # Check table names
        assert StockPrice.__tablename__ == "stock_prices"
        assert StockNewsRelation.__tablename__ == "stock_news_relation"
        assert AccountHolding.__tablename__ == "account_holdings"
        print("??All table names are correct")
        
        # Check that models have required columns
        assert hasattr(StockPrice, 'symbol')
        assert hasattr(StockPrice, 'price')
        assert hasattr(StockNewsRelation, 'stock_symbol')
        assert hasattr(StockNewsRelation, 'article_id')
        assert hasattr(AccountHolding, 'symbol')
        assert hasattr(AccountHolding, 'quantity')
        print("??All required columns are present")
        
        return True
    except AssertionError as e:
        print(f"??Model structure error: {e}")
        return False
    except Exception as e:
        print(f"??Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Stock Data Models Verification")
    print("=" * 60)
    
    results = []
    results.append(test_imports())
    results.append(test_pydantic_schemas())
    results.append(test_database_models())
    
    print("\n" + "=" * 60)
    if all(results):
        print("??All tests passed!")
    else:
        print("??Some tests failed")
    print("=" * 60)
