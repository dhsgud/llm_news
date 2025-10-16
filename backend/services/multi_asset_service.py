"""
Multi-asset management service
Coordinates data collection across stocks, crypto, and forex
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc

try:
    from models.asset_models import Asset, AssetPrice, AssetSentiment, AssetHolding, AssetType
    from models.asset_schemas import AssetDetailResponse, PortfolioSummary
    from services.crypto_data_collector import CryptoDataCollector
    from services.forex_data_collector import ForexDataCollector
except ImportError:
    from models.asset_models import Asset, AssetPrice, AssetSentiment, AssetHolding, AssetType
    from models.asset_schemas import AssetDetailResponse, PortfolioSummary
    from services.crypto_data_collector import CryptoDataCollector
    from services.forex_data_collector import ForexDataCollector

logger = logging.getLogger(__name__)


class MultiAssetService:
    """Service for managing multiple asset types"""
    
    def __init__(self, db: Session, forex_api_key: Optional[str] = None):
        self.db = db
        self.crypto_collector = CryptoDataCollector()
        self.forex_collector = ForexDataCollector(api_key=forex_api_key)
    
    def add_asset(
        self,
        symbol: str,
        name: str,
        asset_type: AssetType,
        exchange: Optional[str] = None,
        base_currency: Optional[str] = None,
        quote_currency: Optional[str] = None
    ) -> Asset:
        """Add a new asset to track"""
        asset = Asset(
            symbol=symbol.upper(),
            name=name,
            asset_type=asset_type,
            exchange=exchange,
            base_currency=base_currency,
            quote_currency=quote_currency
        )
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        logger.info(f"Added new asset: {symbol} ({asset_type})")
        return asset
    
    def get_asset(self, symbol: str, asset_type: Optional[AssetType] = None) -> Optional[Asset]:
        """Get asset by symbol"""
        query = self.db.query(Asset).filter(Asset.symbol == symbol.upper())
        if asset_type:
            query = query.filter(Asset.asset_type == asset_type)
        return query.first()
    
    def list_assets(self, asset_type: Optional[AssetType] = None) -> List[Asset]:
        """List all assets, optionally filtered by type"""
        query = self.db.query(Asset).filter(Asset.is_active == 1)
        if asset_type:
            query = query.filter(Asset.asset_type == asset_type)
        return query.all()
    
    def update_crypto_price(self, asset: Asset) -> Optional[AssetPrice]:
        """Update cryptocurrency price"""
        if asset.asset_type != AssetType.CRYPTO:
            return None
        
        # CoinGecko uses lowercase IDs
        coin_id = asset.symbol.lower()
        price_data = self.crypto_collector.get_price_data(coin_id)
        
        if not price_data:
            return None
        
        asset_price = AssetPrice(
            asset_id=asset.id,
            timestamp=price_data['timestamp'],
            close_price=price_data['current_price'],
            high_price=price_data.get('high_24h'),
            low_price=price_data.get('low_24h'),
            volume=price_data.get('total_volume'),
            market_cap=price_data.get('market_cap')
        )
        
        self.db.add(asset_price)
        self.db.commit()
        self.db.refresh(asset_price)
        return asset_price
    
    def update_forex_rate(self, asset: Asset) -> Optional[AssetPrice]:
        """Update forex exchange rate"""
        if asset.asset_type != AssetType.FOREX:
            return None
        
        if not asset.base_currency or not asset.quote_currency:
            logger.error(f"Forex asset {asset.symbol} missing currency codes")
            return None
        
        rate_data = self.forex_collector.get_exchange_rate(
            asset.base_currency,
            asset.quote_currency
        )
        
        if not rate_data:
            return None
        
        asset_price = AssetPrice(
            asset_id=asset.id,
            timestamp=rate_data['timestamp'],
            close_price=rate_data['rate']
        )
        
        self.db.add(asset_price)
        self.db.commit()
        self.db.refresh(asset_price)
        return asset_price
    
    def update_all_prices(self) -> Dict[str, int]:
        """Update prices for all active assets"""
        stats = {'stock': 0, 'crypto': 0, 'forex': 0, 'errors': 0}
        
        assets = self.list_assets()
        for asset in assets:
            try:
                if asset.asset_type == AssetType.CRYPTO:
                    if self.update_crypto_price(asset):
                        stats['crypto'] += 1
                elif asset.asset_type == AssetType.FOREX:
                    if self.update_forex_rate(asset):
                        stats['forex'] += 1
                # Stock prices handled by existing stock_data_collector
            except Exception as e:
                logger.error(f"Failed to update price for {asset.symbol}: {e}")
                stats['errors'] += 1
        
        logger.info(f"Price update complete: {stats}")
        return stats
    
    def get_latest_price(self, asset_id: int) -> Optional[AssetPrice]:
        """Get latest price for an asset"""
        return self.db.query(AssetPrice)\
            .filter(AssetPrice.asset_id == asset_id)\
            .order_by(desc(AssetPrice.timestamp))\
            .first()
    
    def get_price_history(
        self,
        asset_id: int,
        days: int = 7
    ) -> List[AssetPrice]:
        """Get price history for an asset"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.db.query(AssetPrice)\
            .filter(
                AssetPrice.asset_id == asset_id,
                AssetPrice.timestamp >= cutoff
            )\
            .order_by(AssetPrice.timestamp)\
            .all()
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get portfolio summary across all asset types"""
        holdings = self.db.query(AssetHolding).all()
        
        total_value = 0.0
        total_cost = 0.0
        stock_value = 0.0
        crypto_value = 0.0
        forex_value = 0.0
        
        for holding in holdings:
            # Update current price
            latest_price = self.get_latest_price(holding.asset_id)
            if latest_price:
                holding.current_price = latest_price.close_price
                holding.total_value = holding.quantity * holding.current_price
                cost = holding.quantity * holding.average_price
                holding.profit_loss = holding.total_value - cost
                holding.profit_loss_percent = (holding.profit_loss / cost * 100) if cost > 0 else 0
                
                total_value += holding.total_value
                total_cost += cost
                
                # Categorize by asset type
                if holding.asset.asset_type == AssetType.STOCK:
                    stock_value += holding.total_value
                elif holding.asset.asset_type == AssetType.CRYPTO:
                    crypto_value += holding.total_value
                elif holding.asset.asset_type == AssetType.FOREX:
                    forex_value += holding.total_value
        
        self.db.commit()
        
        total_profit_loss = total_value - total_cost
        total_profit_loss_percent = (total_profit_loss / total_cost * 100) if total_cost > 0 else 0
        
        return PortfolioSummary(
            total_value=total_value,
            total_profit_loss=total_profit_loss,
            total_profit_loss_percent=total_profit_loss_percent,
            stock_value=stock_value,
            crypto_value=crypto_value,
            forex_value=forex_value,
            holdings=holdings
        )
    
    def search_crypto(self, query: str) -> List[Dict]:
        """Search for cryptocurrencies"""
        return self.crypto_collector.search_coin(query)
    
    def get_supported_currencies(self) -> List[str]:
        """Get supported forex currencies"""
        return self.forex_collector.get_supported_currencies()
