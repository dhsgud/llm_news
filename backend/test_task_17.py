"""
Test script for Task 17: Auto Trading Data Models
Tests TradeHistory and AutoTradeConfig models
"""

import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from app.database import SessionLocal
    from models import (
        TradeHistory,
        TradeHistoryCreate,
        AutoTradeConfig,
        AutoTradeConfigCreate,
        TradingConfig,
        Portfolio,
        Holding,
        AutoTradeStatus,
        TradeSignal
    )
except ImportError:
    from app.database import SessionLocal
    from models import (
        TradeHistory,
        TradeHistoryCreate,
        AutoTradeConfig,
        AutoTradeConfigCreate,
        TradingConfig,
        Portfolio,
        Holding,
        AutoTradeStatus,
        TradeSignal
    )


def test_trade_history_model():
    """Test TradeHistory database model"""
    print("\n=== Testing TradeHistory Model ===")
    
    db = SessionLocal()
    try:
        # Create a test trade history record
        trade = TradeHistory(
            order_id="TEST_ORDER_001",
            symbol="005930",
            trade_type="BUY",
            quantity=10,
            executed_price=Decimal("75000.00"),
            total_amount=Decimal("750000.00"),
            executed_at=datetime.now(),
            status="SUCCESS",
            signal_ratio=85,
            reasoning="Strong positive sentiment detected",
            message="Order executed successfully"
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        print(f"??Created TradeHistory record with ID: {trade.id}")
        print(f"  Order ID: {trade.order_id}")
        print(f"  Symbol: {trade.symbol}")
        print(f"  Type: {trade.trade_type}")
        print(f"  Quantity: {trade.quantity}")
        print(f"  Price: {trade.executed_price}")
        print(f"  Total: {trade.total_amount}")
        print(f"  Signal Ratio: {trade.signal_ratio}")
        
        # Query the record
        retrieved = db.query(TradeHistory).filter(
            TradeHistory.order_id == "TEST_ORDER_001"
        ).first()
        
        assert retrieved is not None
        assert retrieved.symbol == "005930"
        assert retrieved.trade_type == "BUY"
        print("??Successfully retrieved TradeHistory record")
        
        # Clean up
        db.delete(trade)
        db.commit()
        print("??Cleaned up test data")
        
        return True
        
    except Exception as e:
        print(f"??Error testing TradeHistory: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_auto_trade_config_model():
    """Test AutoTradeConfig database model"""
    print("\n=== Testing AutoTradeConfig Model ===")
    
    db = SessionLocal()
    try:
        # Create a test config
        config = AutoTradeConfig(
            user_id="test_user_001",
            is_enabled=False,
            max_investment_amount=Decimal("10000000.00"),
            max_position_size=Decimal("2000000.00"),
            risk_level="MEDIUM",
            buy_threshold=80,
            sell_threshold=20,
            stop_loss_percentage=Decimal("5.0"),
            daily_loss_limit=Decimal("500000.00"),
            trading_start_time="09:00",
            trading_end_time="15:30",
            allowed_symbols="005930,000660,035420",
            notification_email="test@example.com",
            notification_enabled=True
        )
        
        db.add(config)
        db.commit()
        db.refresh(config)
        
        print(f"??Created AutoTradeConfig record with ID: {config.id}")
        print(f"  User ID: {config.user_id}")
        print(f"  Enabled: {config.is_enabled}")
        print(f"  Max Investment: {config.max_investment_amount}")
        print(f"  Risk Level: {config.risk_level}")
        print(f"  Buy Threshold: {config.buy_threshold}")
        print(f"  Sell Threshold: {config.sell_threshold}")
        print(f"  Stop Loss: {config.stop_loss_percentage}%")
        
        # Query the record
        retrieved = db.query(AutoTradeConfig).filter(
            AutoTradeConfig.user_id == "test_user_001"
        ).first()
        
        assert retrieved is not None
        assert retrieved.risk_level == "MEDIUM"
        assert retrieved.buy_threshold == 80
        print("??Successfully retrieved AutoTradeConfig record")
        
        # Clean up
        db.delete(config)
        db.commit()
        print("??Cleaned up test data")
        
        return True
        
    except Exception as e:
        print(f"??Error testing AutoTradeConfig: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def test_pydantic_schemas():
    """Test Pydantic schemas"""
    print("\n=== Testing Pydantic Schemas ===")
    
    try:
        # Test TradingConfig schema
        config = TradingConfig(
            max_investment_amount=Decimal("10000000.00"),
            max_position_size=Decimal("2000000.00"),
            risk_level="MEDIUM",
            buy_threshold=80,
            sell_threshold=20,
            stop_loss_percentage=Decimal("5.0"),
            allowed_symbols=["005930", "000660"]
        )
        print("??TradingConfig schema validated")
        
        # Test Holding schema
        holding = Holding(
            symbol="005930",
            quantity=10,
            average_price=Decimal("74000.00"),
            current_price=Decimal("75000.00"),
            total_value=Decimal("750000.00"),
            profit_loss=Decimal("10000.00"),
            profit_loss_percentage=Decimal("1.35")
        )
        print("??Holding schema validated")
        
        # Test Portfolio schema
        portfolio = Portfolio(
            total_value=Decimal("11000000.00"),
            cash_balance=Decimal("9000000.00"),
            invested_amount=Decimal("2000000.00"),
            total_profit_loss=Decimal("50000.00"),
            total_profit_loss_percentage=Decimal("2.5"),
            holdings=[holding],
            updated_at=datetime.now()
        )
        print("??Portfolio schema validated")
        
        # Test AutoTradeStatus schema
        status = AutoTradeStatus(
            is_enabled=True,
            is_running=True,
            last_check_time=datetime.now(),
            total_trades_today=3,
            daily_profit_loss=Decimal("25000.00")
        )
        print("??AutoTradeStatus schema validated")
        
        # Test TradeSignal schema
        signal = TradeSignal(
            symbol="005930",
            signal_ratio=85,
            action="BUY",
            confidence=Decimal("0.82"),
            reasoning="Strong positive sentiment",
            generated_at=datetime.now()
        )
        print("??TradeSignal schema validated")
        
        return True
        
    except Exception as e:
        print(f"??Error testing Pydantic schemas: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Task 17: Auto Trading Data Models Test")
    print("=" * 60)
    
    results = []
    
    # Test database models
    results.append(("TradeHistory Model", test_trade_history_model()))
    results.append(("AutoTradeConfig Model", test_auto_trade_config_model()))
    
    # Test Pydantic schemas
    results.append(("Pydantic Schemas", test_pydantic_schemas()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "??PASSED" if passed else "??FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n??All tests passed!")
        return 0
    else:
        print("\n??Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

