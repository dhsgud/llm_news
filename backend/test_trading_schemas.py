"""
Test script to verify trading schemas work correctly
"""
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_trading_schemas():
    """Test that trading Pydantic schemas work correctly"""
    print("Testing trading schemas...")
    
    # Import directly from the file to avoid __init__.py issues
    import importlib.util
    spec = importlib.util.spec_from_file_location("trading_schemas", backend_dir / "models" / "trading_schemas.py")
    trading_schemas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trading_schemas)
    
    Order = trading_schemas.Order
    TradeResult = trading_schemas.TradeResult
    OrderRequest = trading_schemas.OrderRequest
    OrderResponse = trading_schemas.OrderResponse
    
    try:
        # Test Order
        print("\n1. Testing Order schema:")
        order = Order(
            symbol="005930",
            trade_type="BUY",
            quantity=10,
            price=Decimal("75000.00"),
            order_type="LIMIT"
        )
        print(f"   ??Created: {order.trade_type} {order.quantity} shares of {order.symbol} @ {order.price}")
        print(f"   ??Order type: {order.order_type}")
        
        # Test Order with market order (no price)
        market_order = Order(
            symbol="005930",
            trade_type="SELL",
            quantity=5,
            order_type="MARKET"
        )
        print(f"   ??Market order: {market_order.trade_type} {market_order.quantity} shares")
        
        # Test TradeResult
        print("\n2. Testing TradeResult schema:")
        trade_result = TradeResult(
            order_id="ORD20251007001",
            symbol="005930",
            trade_type="BUY",
            quantity=10,
            executed_price=Decimal("74500.00"),
            total_amount=Decimal("745000.00"),
            executed_at=datetime.now(),
            status="SUCCESS",
            message="Order executed successfully"
        )
        print(f"   ??Order ID: {trade_result.order_id}")
        print(f"   ??Status: {trade_result.status}")
        print(f"   ??Executed: {trade_result.quantity} @ {trade_result.executed_price}")
        print(f"   ??Total: {trade_result.total_amount}")
        
        # Test OrderRequest
        print("\n3. Testing OrderRequest schema:")
        order_request = OrderRequest(
            symbol="005930",
            trade_type="BUY",
            quantity=10,
            price=Decimal("75000.00"),
            signal_ratio=85,
            reasoning="Strong positive sentiment from news analysis"
        )
        print(f"   ??Signal ratio: {order_request.signal_ratio}")
        print(f"   ??Reasoning: {order_request.reasoning}")
        
        # Test OrderResponse
        print("\n4. Testing OrderResponse schema:")
        order_response = OrderResponse(
            success=True,
            order_id="ORD20251007001",
            message="Order submitted successfully",
            trade_result=trade_result
        )
        print(f"   ??Success: {order_response.success}")
        print(f"   ??Message: {order_response.message}")
        
        # Test validation
        print("\n5. Testing validation:")
        try:
            invalid_order = Order(
                symbol="005930",
                trade_type="INVALID",  # Should fail
                quantity=10
            )
            print("   ??Validation should have failed for invalid trade_type")
            return False
        except Exception as e:
            print(f"   ??Validation correctly rejected invalid trade_type")
        
        try:
            invalid_quantity = Order(
                symbol="005930",
                trade_type="BUY",
                quantity=0  # Should fail (must be > 0)
            )
            print("   ??Validation should have failed for zero quantity")
            return False
        except Exception as e:
            print(f"   ??Validation correctly rejected zero quantity")
        
        # Test JSON serialization
        print("\n6. Testing JSON serialization:")
        order_json = order.model_dump_json()
        print(f"   ??Order serialized to JSON: {len(order_json)} bytes")
        
        trade_json = trade_result.model_dump_json()
        print(f"   ??TradeResult serialized to JSON: {len(trade_json)} bytes")
        
        return True
        
    except Exception as e:
        print(f"\n??Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Trading Schemas Verification")
    print("=" * 70)
    
    success = test_trading_schemas()
    
    print("\n" + "=" * 70)
    if success:
        print("??All trading schema tests passed!")
        print("\nThe following schemas are ready to use:")
        print("  - Order: For placing buy/sell orders")
        print("  - TradeResult: For order execution results")
        print("  - OrderRequest: Extended order with AI signal info")
        print("  - OrderResponse: API response wrapper")
    else:
        print("??Some tests failed")
    print("=" * 70)
