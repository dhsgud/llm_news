"""
Multi-Asset Support Demo
Demonstrates cryptocurrency and forex tracking
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from services.multi_asset_service import MultiAssetService
from models.asset_models import AssetType


def demo_crypto_tracking():
    """Demonstrate cryptocurrency tracking"""
    print("\n" + "=" * 60)
    print("Cryptocurrency Tracking Demo")
    print("=" * 60)
    
    db = SessionLocal()
    service = MultiAssetService(db)
    
    try:
        # Add popular cryptocurrencies
        cryptos = [
            ('bitcoin', 'Bitcoin'),
            ('ethereum', 'Ethereum'),
            ('cardano', 'Cardano'),
        ]
        
        print("\n1. Adding cryptocurrencies to track...")
        for coin_id, name in cryptos:
            try:
                asset = service.add_asset(
                    symbol=coin_id.upper(),
                    name=name,
                    asset_type=AssetType.CRYPTO,
                    exchange='CoinGecko'
                )
                print(f"   ??Added {name} ({coin_id.upper()})")
            except Exception as e:
                print(f"   ??{name} already exists or error: {e}")
        
        # Update prices
        print("\n2. Updating cryptocurrency prices...")
        stats = service.update_all_prices()
        print(f"   Updated: {stats['crypto']} crypto assets")
        if stats['errors'] > 0:
            print(f"   Errors: {stats['errors']}")
        
        # Display current prices
        print("\n3. Current cryptocurrency prices:")
        crypto_assets = service.list_assets(asset_type=AssetType.CRYPTO)
        for asset in crypto_assets:
            latest_price = service.get_latest_price(asset.id)
            if latest_price:
                print(f"   {asset.name} ({asset.symbol}): ${latest_price.close_price:,.2f}")
                if latest_price.market_cap:
                    print(f"      Market Cap: ${latest_price.market_cap:,.0f}")
                if latest_price.volume:
                    print(f"      24h Volume: ${latest_price.volume:,.0f}")
        
        # Search for a cryptocurrency
        print("\n4. Searching for 'polkadot'...")
        results = service.search_crypto('polkadot')
        if results:
            print(f"   Found {len(results)} results:")
            for result in results[:3]:
                print(f"   - {result['name']} ({result['symbol'].upper()})")
        
    finally:
        db.close()


def demo_forex_tracking():
    """Demonstrate forex tracking"""
    print("\n" + "=" * 60)
    print("Forex Tracking Demo")
    print("=" * 60)
    
    db = SessionLocal()
    service = MultiAssetService(db)
    
    try:
        # Add popular forex pairs
        forex_pairs = [
            ('USD', 'KRW', 'US Dollar to Korean Won'),
            ('USD', 'EUR', 'US Dollar to Euro'),
            ('USD', 'JPY', 'US Dollar to Japanese Yen'),
            ('EUR', 'GBP', 'Euro to British Pound'),
        ]
        
        print("\n1. Adding forex pairs to track...")
        for base, quote, name in forex_pairs:
            try:
                symbol = f"{base}/{quote}"
                asset = service.add_asset(
                    symbol=symbol,
                    name=name,
                    asset_type=AssetType.FOREX,
                    base_currency=base,
                    quote_currency=quote
                )
                print(f"   ??Added {symbol}")
            except Exception as e:
                print(f"   ??{symbol} already exists or error: {e}")
        
        # Update rates
        print("\n2. Updating forex rates...")
        stats = service.update_all_prices()
        print(f"   Updated: {stats['forex']} forex pairs")
        if stats['errors'] > 0:
            print(f"   Errors: {stats['errors']}")
        
        # Display current rates
        print("\n3. Current exchange rates:")
        forex_assets = service.list_assets(asset_type=AssetType.FOREX)
        for asset in forex_assets:
            latest_price = service.get_latest_price(asset.id)
            if latest_price:
                print(f"   {asset.symbol}: {latest_price.close_price:.4f}")
                print(f"      (1 {asset.base_currency} = {latest_price.close_price:.4f} {asset.quote_currency})")
        
        # Get supported currencies
        print("\n4. Supported currencies:")
        currencies = service.get_supported_currencies()
        print(f"   {len(currencies)} currencies available")
        print(f"   Sample: {', '.join(currencies[:10])}")
        
    finally:
        db.close()


def demo_portfolio_summary():
    """Demonstrate portfolio summary"""
    print("\n" + "=" * 60)
    print("Portfolio Summary Demo")
    print("=" * 60)
    
    db = SessionLocal()
    service = MultiAssetService(db)
    
    try:
        # Note: This requires holdings to be added manually or through trading
        print("\n1. Getting portfolio summary...")
        summary = service.get_portfolio_summary()
        
        print(f"\n   Total Portfolio Value: ${summary.total_value:,.2f}")
        print(f"   Total P&L: ${summary.total_profit_loss:,.2f} ({summary.total_profit_loss_percent:.2f}%)")
        print(f"\n   Breakdown by Asset Type:")
        print(f"   - Stocks: ${summary.stock_value:,.2f}")
        print(f"   - Crypto: ${summary.crypto_value:,.2f}")
        print(f"   - Forex: ${summary.forex_value:,.2f}")
        
        if summary.holdings:
            print(f"\n   Holdings ({len(summary.holdings)}):")
            for holding in summary.holdings:
                print(f"   - {holding.asset.name} ({holding.asset.symbol})")
                print(f"     Quantity: {holding.quantity}")
                print(f"     Avg Price: ${holding.average_price:,.2f}")
                if holding.current_price:
                    print(f"     Current: ${holding.current_price:,.2f}")
                if holding.profit_loss:
                    print(f"     P&L: ${holding.profit_loss:,.2f} ({holding.profit_loss_percent:.2f}%)")
        else:
            print("\n   No holdings found. Add holdings through the API or trading system.")
        
    finally:
        db.close()


def demo_price_history():
    """Demonstrate price history retrieval"""
    print("\n" + "=" * 60)
    print("Price History Demo")
    print("=" * 60)
    
    db = SessionLocal()
    service = MultiAssetService(db)
    
    try:
        # Get Bitcoin if it exists
        asset = service.get_asset('BITCOIN', asset_type=AssetType.CRYPTO)
        if not asset:
            print("\n   Bitcoin not found. Run crypto tracking demo first.")
            return
        
        print(f"\n1. Getting 7-day price history for {asset.name}...")
        history = service.get_price_history(asset.id, days=7)
        
        if history:
            print(f"   Found {len(history)} price points")
            print("\n   Recent prices:")
            for price in history[-5:]:  # Last 5 prices
                print(f"   {price.timestamp}: ${price.close_price:,.2f}")
        else:
            print("   No price history available yet.")
        
    finally:
        db.close()


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("Multi-Asset Support Demo")
    print("=" * 60)
    print("\nThis demo shows how to use the multi-asset tracking system")
    print("for cryptocurrencies and forex pairs.")
    
    try:
        # Run demos
        demo_crypto_tracking()
        demo_forex_tracking()
        demo_portfolio_summary()
        demo_price_history()
        
        print("\n" + "=" * 60)
        print("Demo Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Check the API documentation at http://localhost:8000/docs")
        print("2. Use the /api/assets endpoints to manage assets")
        print("3. Set up scheduled price updates")
        print("4. Integrate with the frontend dashboard")
        
    except Exception as e:
        print(f"\n??Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
