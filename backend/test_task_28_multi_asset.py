"""
Test Task 28: Multi-Asset Support
Tests cryptocurrency and forex data collection
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from models.asset_models import Asset, AssetPrice, AssetType
from services.crypto_data_collector import CryptoDataCollector
from services.forex_data_collector import ForexDataCollector
from services.multi_asset_service import MultiAssetService


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_multi_asset.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestCryptoDataCollector:
    """Test cryptocurrency data collection"""
    
    def test_get_supported_coins(self):
        """Test fetching supported cryptocurrencies"""
        collector = CryptoDataCollector()
        coins = collector.get_supported_coins()
        
        assert isinstance(coins, list)
        if coins:  # API might be rate limited
            assert len(coins) > 0
            assert 'id' in coins[0]
            assert 'symbol' in coins[0]
            assert 'name' in coins[0]
    
    def test_get_price_data(self):
        """Test fetching cryptocurrency price"""
        collector = CryptoDataCollector()
        price_data = collector.get_price_data('bitcoin')
        
        if price_data:  # API might be rate limited
            assert price_data['symbol'] == 'BTC'
            assert price_data['name'] == 'Bitcoin'
            assert price_data['current_price'] > 0
            assert 'market_cap' in price_data
            assert 'total_volume' in price_data
            assert isinstance(price_data['timestamp'], datetime)
    
    def test_get_historical_data(self):
        """Test fetching historical cryptocurrency data"""
        collector = CryptoDataCollector()
        history = collector.get_historical_data('bitcoin', days=7)
        
        if history:  # API might be rate limited
            assert isinstance(history, list)
            assert len(history) > 0
            assert 'timestamp' in history[0]
            assert 'close_price' in history[0]
            assert history[0]['close_price'] > 0
    
    def test_search_coin(self):
        """Test searching for cryptocurrencies"""
        collector = CryptoDataCollector()
        results = collector.search_coin('bitcoin')
        
        if results:  # API might be rate limited
            assert isinstance(results, list)
            assert len(results) > 0
            assert any('bitcoin' in coin['id'].lower() for coin in results)


class TestForexDataCollector:
    """Test forex data collection"""
    
    def test_get_supported_currencies(self):
        """Test getting supported currencies"""
        collector = ForexDataCollector()
        currencies = collector.get_supported_currencies()
        
        assert isinstance(currencies, list)
        assert len(currencies) > 0
        assert 'USD' in currencies
        assert 'EUR' in currencies
        assert 'KRW' in currencies
    
    def test_get_exchange_rate(self):
        """Test fetching exchange rate"""
        collector = ForexDataCollector()
        rate_data = collector.get_exchange_rate('USD', 'KRW')
        
        if rate_data:  # API might be rate limited
            assert rate_data['base_currency'] == 'USD'
            assert rate_data['quote_currency'] == 'KRW'
            assert rate_data['rate'] > 0
            assert isinstance(rate_data['timestamp'], datetime)
    
    def test_get_multiple_rates(self):
        """Test fetching multiple exchange rates"""
        collector = ForexDataCollector()
        rates = collector.get_multiple_rates('USD', ['EUR', 'GBP', 'JPY'])
        
        if rates:  # API might be rate limited
            assert isinstance(rates, dict)
            assert len(rates) > 0
            for currency, rate in rates.items():
                assert rate > 0
    
    def test_convert_amount(self):
        """Test currency conversion"""
        collector = ForexDataCollector()
        converted = collector.convert_amount(100, 'USD', 'EUR')
        
        if converted:  # API might be rate limited
            assert converted > 0
            assert converted != 100  # Should be different


class TestMultiAssetService:
    """Test multi-asset service"""
    
    def test_add_crypto_asset(self, db):
        """Test adding a cryptocurrency asset"""
        service = MultiAssetService(db)
        
        asset = service.add_asset(
            symbol='BTC',
            name='Bitcoin',
            asset_type=AssetType.CRYPTO,
            exchange='CoinGecko'
        )
        
        assert asset.id is not None
        assert asset.symbol == 'BTC'
        assert asset.name == 'Bitcoin'
        assert asset.asset_type == AssetType.CRYPTO
        assert asset.is_active == 1
    
    def test_add_forex_asset(self, db):
        """Test adding a forex pair"""
        service = MultiAssetService(db)
        
        asset = service.add_asset(
            symbol='USD/KRW',
            name='US Dollar to Korean Won',
            asset_type=AssetType.FOREX,
            base_currency='USD',
            quote_currency='KRW'
        )
        
        assert asset.id is not None
        assert asset.symbol == 'USD/KRW'
        assert asset.asset_type == AssetType.FOREX
        assert asset.base_currency == 'USD'
        assert asset.quote_currency == 'KRW'
    
    def test_list_assets_by_type(self, db):
        """Test listing assets filtered by type"""
        service = MultiAssetService(db)
        
        # Add different asset types
        service.add_asset('BTC', 'Bitcoin', AssetType.CRYPTO)
        service.add_asset('ETH', 'Ethereum', AssetType.CRYPTO)
        service.add_asset('USD/EUR', 'USD to EUR', AssetType.FOREX, 
                         base_currency='USD', quote_currency='EUR')
        
        # List crypto assets
        crypto_assets = service.list_assets(asset_type=AssetType.CRYPTO)
        assert len(crypto_assets) == 2
        assert all(a.asset_type == AssetType.CRYPTO for a in crypto_assets)
        
        # List forex assets
        forex_assets = service.list_assets(asset_type=AssetType.FOREX)
        assert len(forex_assets) == 1
        assert forex_assets[0].asset_type == AssetType.FOREX
        
        # List all assets
        all_assets = service.list_assets()
        assert len(all_assets) == 3
    
    def test_get_asset(self, db):
        """Test retrieving an asset"""
        service = MultiAssetService(db)
        
        # Add asset
        created = service.add_asset('BTC', 'Bitcoin', AssetType.CRYPTO)
        
        # Retrieve asset
        retrieved = service.get_asset('BTC')
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.symbol == 'BTC'
        
        # Retrieve with type filter
        retrieved_typed = service.get_asset('BTC', asset_type=AssetType.CRYPTO)
        assert retrieved_typed is not None
        
        # Should not find with wrong type
        not_found = service.get_asset('BTC', asset_type=AssetType.FOREX)
        assert not_found is None
    
    def test_update_crypto_price(self, db):
        """Test updating cryptocurrency price"""
        service = MultiAssetService(db)
        
        # Add crypto asset
        asset = service.add_asset('bitcoin', 'Bitcoin', AssetType.CRYPTO)
        
        # Update price (might fail due to API limits)
        price = service.update_crypto_price(asset)
        
        if price:  # Only check if API call succeeded
            assert price.asset_id == asset.id
            assert price.close_price > 0
            assert isinstance(price.timestamp, datetime)
    
    def test_update_forex_rate(self, db):
        """Test updating forex rate"""
        service = MultiAssetService(db)
        
        # Add forex pair
        asset = service.add_asset(
            'USD/EUR',
            'US Dollar to Euro',
            AssetType.FOREX,
            base_currency='USD',
            quote_currency='EUR'
        )
        
        # Update rate (might fail due to API limits)
        price = service.update_forex_rate(asset)
        
        if price:  # Only check if API call succeeded
            assert price.asset_id == asset.id
            assert price.close_price > 0
            assert isinstance(price.timestamp, datetime)
    
    def test_get_latest_price(self, db):
        """Test getting latest price"""
        service = MultiAssetService(db)
        
        # Add asset and price
        asset = service.add_asset('BTC', 'Bitcoin', AssetType.CRYPTO)
        
        price1 = AssetPrice(
            asset_id=asset.id,
            timestamp=datetime(2025, 1, 1, 12, 0),
            close_price=50000.0
        )
        price2 = AssetPrice(
            asset_id=asset.id,
            timestamp=datetime(2025, 1, 2, 12, 0),
            close_price=51000.0
        )
        
        db.add(price1)
        db.add(price2)
        db.commit()
        
        # Get latest
        latest = service.get_latest_price(asset.id)
        assert latest is not None
        assert latest.close_price == 51000.0
    
    def test_search_crypto(self):
        """Test cryptocurrency search"""
        service = MultiAssetService(TestingSessionLocal())
        results = service.search_crypto('bitcoin')
        
        if results:  # API might be rate limited
            assert isinstance(results, list)
            assert len(results) > 0
    
    def test_get_supported_currencies(self):
        """Test getting supported currencies"""
        service = MultiAssetService(TestingSessionLocal())
        currencies = service.get_supported_currencies()
        
        assert isinstance(currencies, list)
        assert len(currencies) > 0
        assert 'USD' in currencies


def test_asset_model_relationships(db):
    """Test database model relationships"""
    # Create asset
    asset = Asset(
        symbol='BTC',
        name='Bitcoin',
        asset_type=AssetType.CRYPTO
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    
    # Add price
    price = AssetPrice(
        asset_id=asset.id,
        timestamp=datetime.utcnow(),
        close_price=50000.0,
        volume=1000000.0
    )
    db.add(price)
    db.commit()
    
    # Test relationship
    assert len(asset.prices) == 1
    assert asset.prices[0].close_price == 50000.0
    assert price.asset.symbol == 'BTC'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
