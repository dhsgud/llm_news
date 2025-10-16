"""
Brokerage API Usage Example

This example demonstrates how to use the brokerage API connectors
to interact with Korea Investment Securities API.

Requirements: 11.1, 11.2, 11.6
"""

import os
import sys
from pathlib import Path
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.korea_investment_api import KoreaInvestmentAPI
from models.trading_schemas import Order


def main():
    """
    Example usage of Korea Investment API
    """
    
    print("=" * 60)
    print("Korea Investment API Example")
    print("=" * 60)
    
    # Initialize API client
    # Note: Set these environment variables in your .env file
    api = KoreaInvestmentAPI(
        app_key=os.getenv("KOREA_INVESTMENT_APP_KEY", "YOUR_APP_KEY"),
        app_secret=os.getenv("KOREA_INVESTMENT_APP_SECRET", "YOUR_APP_SECRET"),
        account_number=os.getenv("KOREA_INVESTMENT_ACCOUNT_NUMBER", "12345678"),
        account_product_code=os.getenv("KOREA_INVESTMENT_ACCOUNT_PRODUCT_CODE", "01"),
        use_virtual=True  # Use virtual trading for testing
    )
    
    # Step 1: Authenticate
    print("\n1. Authenticating...")
    if not api.authenticate():
        print("??Authentication failed!")
        return
    
    print("??Authentication successful!")
    print(f"   Token expires at: {api.token_expires_at}")
    
    # Step 2: Get stock price
    print("\n2. Getting stock price for Samsung Electronics (005930)...")
    try:
        price = api.get_stock_price("005930")
        print(f"??Stock Price Retrieved:")
        print(f"   Symbol: {price.symbol}")
        print(f"   Current Price: ??price.price:,}")
        print(f"   Volume: {price.volume:,}")
        print(f"   Open: ??price.open_price:,}")
        print(f"   High: ??price.high_price:,}")
        print(f"   Low: ??price.low_price:,}")
        print(f"   Timestamp: {price.timestamp}")
    except Exception as e:
        print(f"??Failed to get stock price: {e}")
    
    # Step 3: Get account balance
    print("\n3. Getting account balance...")
    try:
        balance = api.get_account_balance()
        print(f"??Account Balance Retrieved:")
        print(f"   Account Number: {balance.account_number}")
        print(f"   Total Balance: ??balance.balance:,}")
        print(f"   Available Cash: ??balance.available_cash:,}")
        print(f"   Total Assets: ??balance.total_assets:,}")
    except Exception as e:
        print(f"??Failed to get account balance: {e}")
    
    # Step 4: Get account holdings
    print("\n4. Getting account holdings...")
    try:
        holdings = api.get_account_holdings()
        if holdings:
            print(f"??Holdings Retrieved ({len(holdings)} stocks):")
            for holding in holdings:
                print(f"\n   {holding['name']} ({holding['symbol']})")
                print(f"   - Quantity: {holding['quantity']:,} shares")
                print(f"   - Avg Price: ??holding['average_price']:,}")
                print(f"   - Current Price: ??holding['current_price']:,}")
                print(f"   - Evaluation: ??holding['evaluation_amount']:,}")
                print(f"   - P/L: ??holding['profit_loss']:,} ({holding['profit_loss_rate']}%)")
        else:
            print("   No holdings found")
    except Exception as e:
        print(f"??Failed to get holdings: {e}")
    
    # Step 5: Place a test order (commented out for safety)
    print("\n5. Placing order (DEMO - not executed)...")
    print("   To actually place an order, uncomment the code below")
    
    # UNCOMMENT TO ACTUALLY PLACE AN ORDER (USE WITH CAUTION!)
    # order = Order(
    #     symbol="005930",
    #     trade_type="BUY",
    #     quantity=1,
    #     price=Decimal("75000"),
    #     order_type="LIMIT"
    # )
    # 
    # try:
    #     result = api.place_order(order)
    #     print(f"Order Status: {result.status}")
    #     print(f"Order ID: {result.order_id}")
    #     print(f"Message: {result.message}")
    #     
    #     if result.status == "SUCCESS":
    #         print(f"??Order placed successfully!")
    #         print(f"   Symbol: {result.symbol}")
    #         print(f"   Type: {result.trade_type}")
    #         print(f"   Quantity: {result.quantity}")
    #         print(f"   Price: ??result.executed_price:,}")
    #         print(f"   Total: ??result.total_amount:,}")
    #     else:
    #         print(f"??Order failed: {result.message}")
    # except Exception as e:
    #     print(f"??Failed to place order: {e}")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    main()
