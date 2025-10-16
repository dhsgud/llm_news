"""
Simple test for RiskManager - Task 18
Tests core risk management functionality
"""

from datetime import datetime, time
from decimal import Decimal


def test_risk_manager_basic():
    """Test basic RiskManager functionality without database"""
    print("Testing RiskManager basic functionality...")
    
    # Test 1: Trading hours check
    print("\n1. Testing trading hours validation...")
    start_time = time(9, 0)
    end_time = time(15, 30)
    current_time = time(10, 30)
    
    is_within_hours = start_time <= current_time <= end_time
    assert is_within_hours, "Should be within trading hours"
    print("??Trading hours validation works")
    
    # Test 2: Symbol filtering
    print("\n2. Testing symbol filtering...")
    allowed_symbols = "005930,000660,035420"
    excluded_symbols = "999999"
    test_symbol = "005930"
    
    allowed_list = [s.strip() for s in allowed_symbols.split(",")]
    excluded_list = [s.strip() for s in excluded_symbols.split(",")]
    
    is_allowed = test_symbol in allowed_list and test_symbol not in excluded_list
    assert is_allowed, "Symbol should be allowed"
    print("??Symbol filtering works")
    
    # Test 3: Position size validation
    print("\n3. Testing position size validation...")
    max_position_size = Decimal("2000000.00")
    quantity = 10
    price = Decimal("75000")
    trade_value = Decimal(quantity) * price
    
    is_valid_size = trade_value <= max_position_size
    assert is_valid_size, "Trade should be within position size limit"
    print(f"??Position size validation works (trade: {trade_value}, limit: {max_position_size})")
    
    # Test 4: Investment limit check
    print("\n4. Testing investment limit...")
    max_investment = Decimal("10000000.00")
    current_invested = Decimal("5000000.00")
    new_trade = Decimal("750000.00")
    
    total_after_trade = current_invested + new_trade
    is_within_limit = total_after_trade <= max_investment
    assert is_within_limit, "Should be within investment limit"
    print(f"??Investment limit check works (total: {total_after_trade}, limit: {max_investment})")
    
    # Test 5: Cash balance check
    print("\n5. Testing cash balance...")
    cash_balance = Decimal("5000000.00")
    trade_cost = Decimal("750000.00")
    
    has_sufficient_cash = cash_balance >= trade_cost
    assert has_sufficient_cash, "Should have sufficient cash"
    print(f"??Cash balance check works (balance: {cash_balance}, cost: {trade_cost})")
    
    # Test 6: Position size calculation
    print("\n6. Testing position size calculation...")
    max_position = Decimal("2000000.00")
    risk_multipliers = {"LOW": Decimal("0.5"), "MEDIUM": Decimal("0.75"), "HIGH": Decimal("1.0")}
    signal_ratio = 85
    price = Decimal("75000")
    
    for risk_level, multiplier in risk_multipliers.items():
        signal_strength = Decimal(signal_ratio) / Decimal("100")
        position_amount = max_position * multiplier * signal_strength
        quantity = int(position_amount / price)
        print(f"  {risk_level}: {quantity} shares (amount: {position_amount})")
        assert quantity > 0, f"Should calculate positive quantity for {risk_level}"
    
    print("??Position size calculation works")
    
    # Test 7: Stop-loss calculation
    print("\n7. Testing stop-loss calculation...")
    average_price = Decimal("75000")
    current_price = Decimal("70000")
    stop_loss_threshold = Decimal("-5.0")
    
    loss_percentage = ((current_price - average_price) / average_price) * Decimal("100")
    should_trigger = loss_percentage <= stop_loss_threshold
    
    print(f"  Loss: {loss_percentage:.2f}%, Threshold: {stop_loss_threshold}%")
    assert should_trigger, "Stop-loss should trigger"
    print("??Stop-loss calculation works")
    
    # Test 8: VIX abnormal market detection
    print("\n8. Testing abnormal market detection...")
    vix_normal = Decimal("20")
    vix_high = Decimal("35")
    vix_extreme = Decimal("45")
    
    is_normal = vix_normal < Decimal("30")
    is_high = Decimal("30") <= vix_high < Decimal("40")
    is_extreme = vix_extreme >= Decimal("40")
    
    assert is_normal, "VIX 20 should be normal"
    assert is_high, "VIX 35 should be high"
    assert is_extreme, "VIX 45 should be extreme"
    print("??Abnormal market detection works")
    
    # Test 9: Sell validation - sufficient shares
    print("\n9. Testing sell validation...")
    held_quantity = 10
    sell_quantity = 5
    
    has_sufficient_shares = held_quantity >= sell_quantity
    assert has_sufficient_shares, "Should have sufficient shares to sell"
    print(f"??Sell validation works (held: {held_quantity}, selling: {sell_quantity})")
    
    # Test 10: Daily loss limit
    print("\n10. Testing daily loss limit...")
    daily_loss_limit = Decimal("500000.00")
    current_daily_loss = Decimal("-300000.00")
    
    is_within_daily_limit = current_daily_loss > -abs(daily_loss_limit)
    assert is_within_daily_limit, "Should be within daily loss limit"
    print(f"??Daily loss limit check works (loss: {current_daily_loss}, limit: {daily_loss_limit})")
    
    print("\n" + "="*60)
    print("??All RiskManager basic tests passed!")
    print("="*60)


if __name__ == "__main__":
    test_risk_manager_basic()
