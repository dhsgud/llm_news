"""
Test suite for Task 22.1: Caching Strategy Implementation
Tests Redis integration, database fallback, and cache services
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from app.database import Base
from services.cache_manager import CacheManager
from services.stock_price_cache import StockPriceCache
from services.analysis_cache_service import AnalysisCacheService
from models.analysis_cache import AnalysisCache
from models.stock_price import StockPrice


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test_cache.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestCacheManager:
    """Test CacheManager basic functionality"""
    
    def test_cache_manager_initialization(self, db_session):
        """Test cache manager initializes correctly"""
        cache_manager = CacheManager(db_session)
        assert cache_manager is not None
        assert cache_manager.db == db_session
    
    def test_set_and_get_simple_value(self, db_session):
        """Test setting and getting a simple value"""
        cache_manager = CacheManager(db_session)
        
        # Set a value
        success = cache_manager.set("test_key", "test_value", ttl_hours=1)
        assert success is True
        
        # Get the value
        value = cache_manager.get("test_key")
        assert value is not None
        assert value["value"] == "test_value"
    
    def test_set_and_get_dict_value(self, db_session):
        """Test setting and getting a dictionary value"""
        cache_manager = CacheManager(db_session)
        
        test_data = {
            "name": "Test",
            "value": 123,
            "nested": {"key": "value"}
        }
        
        success = cache_manager.set("test_dict", test_data, ttl_hours=1)
        assert success is True
        
        value = cache_manager.get("test_dict")
        assert value is not None
        assert value["name"] == "Test"
        assert value["value"] == 123
        assert value["nested"]["key"] == "value"
    
    def test_cache_expiry(self, db_session):
        """Test that expired cache entries are not returned"""
        cache_manager = CacheManager(db_session)
        
        # Set a value with very short TTL
        success = cache_manager.set("expire_test", "value", ttl_seconds=1)
        assert success is True
        
        # Should be available immediately
        value = cache_manager.get("expire_test")
        assert value is not None
        
        # Wait for expiry
        import time
        time.sleep(2)
        
        # Should be expired now
        value = cache_manager.get("expire_test")
        assert value is None
    
    def test_cache_update(self, db_session):
        """Test updating an existing cache entry"""
        cache_manager = CacheManager(db_session)
        
        # Set initial value
        cache_manager.set("update_test", "initial", ttl_hours=1)
        value = cache_manager.get("update_test")
        assert value["value"] == "initial"
        
        # Update value
        cache_manager.set("update_test", "updated", ttl_hours=1)
        value = cache_manager.get("update_test")
        assert value["value"] == "updated"
    
    def test_cache_delete(self, db_session):
        """Test deleting a cache entry"""
        cache_manager = CacheManager(db_session)
        
        # Set a value
        cache_manager.set("delete_test", "value", ttl_hours=1)
        assert cache_manager.get("delete_test") is not None
        
        # Delete it
        success = cache_manager.delete("delete_test")
        assert success is True
        
        # Should be gone
        assert cache_manager.get("delete_test") is None
    
    def test_clear_expired(self, db_session):
        """Test clearing expired cache entries"""
        cache_manager = CacheManager(db_session)
        
        # Create some expired entries
        for i in range(3):
            cache_entry = AnalysisCache(
                cache_key=f"expired_{i}",
                result_json={"value": i},
                expires_at=datetime.now() - timedelta(hours=1)
            )
            db_session.add(cache_entry)
        
        # Create some valid entries
        for i in range(2):
            cache_entry = AnalysisCache(
                cache_key=f"valid_{i}",
                result_json={"value": i},
                expires_at=datetime.now() + timedelta(hours=1)
            )
            db_session.add(cache_entry)
        
        db_session.commit()
        
        # Clear expired
        count = cache_manager.clear_expired()
        assert count == 3
        
        # Valid entries should still exist
        assert cache_manager.get("valid_0") is not None
        assert cache_manager.get("valid_1") is not None
    
    def test_clear_all(self, db_session):
        """Test clearing all cache entries"""
        cache_manager = CacheManager(db_session)
        
        # Set multiple values
        cache_manager.set("key1", "value1", ttl_hours=1)
        cache_manager.set("key2", "value2", ttl_hours=1)
        cache_manager.set("key3", "value3", ttl_hours=1)
        
        # Clear all
        success = cache_manager.clear_all()
        assert success is True
        
        # All should be gone
        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
        assert cache_manager.get("key3") is None
    
    def test_clear_pattern(self, db_session):
        """Test clearing cache entries matching a pattern"""
        cache_manager = CacheManager(db_session)
        
        # Set values with different prefixes
        cache_manager.set("analysis:market", "value1", ttl_hours=1)
        cache_manager.set("analysis:stock", "value2", ttl_hours=1)
        cache_manager.set("price:AAPL", "value3", ttl_hours=1)
        
        # Clear only analysis entries
        success = cache_manager.clear_all("analysis:*")
        assert success is True
        
        # Analysis entries should be gone
        assert cache_manager.get("analysis:market") is None
        assert cache_manager.get("analysis:stock") is None
        
        # Price entry should still exist
        assert cache_manager.get("price:AAPL") is not None
    
    def test_get_stats(self, db_session):
        """Test getting cache statistics"""
        cache_manager = CacheManager(db_session)
        
        # Add some entries
        cache_manager.set("key1", "value1", ttl_hours=1)
        cache_manager.set("key2", "value2", ttl_hours=1)
        
        stats = cache_manager.get_stats()
        assert stats is not None
        assert "database_entries" in stats
        assert stats["database_entries"] >= 2


class TestStockPriceCache:
    """Test StockPriceCache functionality"""
    
    def test_stock_price_cache_initialization(self, db_session):
        """Test stock price cache initializes correctly"""
        stock_cache = StockPriceCache(db_session)
        assert stock_cache is not None
        assert stock_cache.CACHE_TTL_SECONDS == 60
    
    def test_set_and_get_stock_price(self, db_session):
        """Test caching stock price"""
        stock_cache = StockPriceCache(db_session)
        
        # Set price
        success = stock_cache.set_price(
            symbol="AAPL",
            price=150.50,
            volume=1000000,
            open_price=149.00,
            high_price=151.00,
            low_price=148.50
        )
        assert success is True
        
        # Get price
        price_data = stock_cache.get_price("AAPL")
        assert price_data is not None
        assert price_data["symbol"] == "AAPL"
        assert price_data["price"] == 150.50
        assert price_data["volume"] == 1000000
    
    def test_stock_price_case_insensitive(self, db_session):
        """Test that stock symbols are case-insensitive"""
        stock_cache = StockPriceCache(db_session)
        
        stock_cache.set_price(symbol="aapl", price=150.00)
        
        # Should work with different cases
        assert stock_cache.get_price("AAPL") is not None
        assert stock_cache.get_price("aapl") is not None
        assert stock_cache.get_price("Aapl") is not None
    
    def test_invalidate_stock_price(self, db_session):
        """Test invalidating stock price cache"""
        stock_cache = StockPriceCache(db_session)
        
        stock_cache.set_price(symbol="AAPL", price=150.00)
        assert stock_cache.get_price("AAPL") is not None
        
        success = stock_cache.invalidate_price("AAPL")
        assert success is True
        assert stock_cache.get_price("AAPL") is None
    
    def test_clear_all_prices(self, db_session):
        """Test clearing all stock prices"""
        stock_cache = StockPriceCache(db_session)
        
        stock_cache.set_price(symbol="AAPL", price=150.00)
        stock_cache.set_price(symbol="GOOGL", price=2800.00)
        stock_cache.set_price(symbol="MSFT", price=300.00)
        
        success = stock_cache.clear_all_prices()
        assert success is True
        
        assert stock_cache.get_price("AAPL") is None
        assert stock_cache.get_price("GOOGL") is None
        assert stock_cache.get_price("MSFT") is None


class TestAnalysisCacheService:
    """Test AnalysisCacheService functionality"""
    
    def test_analysis_cache_initialization(self, db_session):
        """Test analysis cache service initializes correctly"""
        analysis_cache = AnalysisCacheService(db_session)
        assert analysis_cache is not None
        assert analysis_cache.CACHE_TTL_HOURS == 1
    
    def test_market_analysis_cache(self, db_session):
        """Test caching market analysis"""
        analysis_cache = AnalysisCacheService(db_session)
        
        # Set market analysis
        success = analysis_cache.set_market_analysis(
            asset_type="general",
            buy_sell_ratio=75,
            trend_summary="Market is bullish",
            vix=15.5,
            confidence="high"
        )
        assert success is True
        
        # Get market analysis
        result = analysis_cache.get_market_analysis("general")
        assert result is not None
        assert result["buy_sell_ratio"] == 75
        assert result["trend_summary"] == "Market is bullish"
        assert result["vix"] == 15.5
    
    def test_stock_sentiment_cache(self, db_session):
        """Test caching stock sentiment"""
        analysis_cache = AnalysisCacheService(db_session)
        
        # Set sentiment
        success = analysis_cache.set_stock_sentiment(
            symbol="AAPL",
            sentiment="Positive",
            score=1.0,
            reasoning="Strong earnings report",
            related_news_count=5
        )
        assert success is True
        
        # Get sentiment
        result = analysis_cache.get_stock_sentiment("AAPL")
        assert result is not None
        assert result["symbol"] == "AAPL"
        assert result["sentiment"] == "Positive"
        assert result["score"] == 1.0
    
    def test_trend_summary_cache(self, db_session):
        """Test caching trend summary"""
        analysis_cache = AnalysisCacheService(db_session)
        
        # Set trend summary
        success = analysis_cache.set_trend_summary(
            summary_text="Overall positive trend",
            dominant_sentiment="Positive",
            key_drivers=["Strong earnings", "Economic growth"],
            days=7
        )
        assert success is True
        
        # Get trend summary
        result = analysis_cache.get_trend_summary(days=7)
        assert result is not None
        assert result["summary_text"] == "Overall positive trend"
        assert result["dominant_sentiment"] == "Positive"
        assert len(result["key_drivers"]) == 2
    
    def test_daily_sentiment_cache(self, db_session):
        """Test caching daily sentiment scores"""
        analysis_cache = AnalysisCacheService(db_session)
        
        daily_scores = [
            {"date": "2025-10-01", "score": 0.5},
            {"date": "2025-10-02", "score": -0.3},
            {"date": "2025-10-03", "score": 0.8}
        ]
        
        # Set daily sentiment
        success = analysis_cache.set_daily_sentiment(daily_scores, days=3)
        assert success is True
        
        # Get daily sentiment
        result = analysis_cache.get_daily_sentiment(days=3)
        assert result is not None
        assert "daily_scores" in result
        assert len(result["daily_scores"]) == 3
    
    def test_invalidate_market_analysis(self, db_session):
        """Test invalidating market analysis cache"""
        analysis_cache = AnalysisCacheService(db_session)
        
        analysis_cache.set_market_analysis(
            asset_type="general",
            buy_sell_ratio=75,
            trend_summary="Test",
            vix=15.0
        )
        
        assert analysis_cache.get_market_analysis("general") is not None
        
        success = analysis_cache.invalidate_market_analysis("general")
        assert success is True
        assert analysis_cache.get_market_analysis("general") is None
    
    def test_invalidate_all_analysis(self, db_session):
        """Test invalidating all analysis caches"""
        analysis_cache = AnalysisCacheService(db_session)
        
        # Set multiple analysis results
        analysis_cache.set_market_analysis("general", 75, "Test", 15.0)
        analysis_cache.set_stock_sentiment("AAPL", "Positive", 1.0, "Test")
        analysis_cache.set_trend_summary("Test", "Positive", ["Test"], 7)
        
        # Invalidate all
        success = analysis_cache.invalidate_all_analysis()
        assert success is True
        
        # All should be gone
        assert analysis_cache.get_market_analysis("general") is None
        assert analysis_cache.get_stock_sentiment("AAPL") is None
        assert analysis_cache.get_trend_summary(7) is None


def test_cache_integration(db_session):
    """Test integration between different cache services"""
    cache_manager = CacheManager(db_session)
    stock_cache = StockPriceCache(db_session)
    analysis_cache = AnalysisCacheService(db_session)
    
    # Set data in different caches
    stock_cache.set_price("AAPL", 150.00)
    analysis_cache.set_stock_sentiment("AAPL", "Positive", 1.0, "Test")
    analysis_cache.set_market_analysis("general", 75, "Bullish", 15.0)
    
    # Verify all data is accessible
    assert stock_cache.get_price("AAPL") is not None
    assert analysis_cache.get_stock_sentiment("AAPL") is not None
    assert analysis_cache.get_market_analysis("general") is not None
    
    # Get stats
    stats = cache_manager.get_stats()
    assert stats["database_entries"] >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
