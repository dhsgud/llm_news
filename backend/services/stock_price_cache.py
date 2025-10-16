"""
Stock Price Caching Service
Implements 1-minute caching for stock prices to reduce API calls
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

try:
    from services.cache_manager import CacheManager
    from models.stock_price import StockPrice
except ImportError:
    from services.cache_manager import CacheManager
    from models.stock_price import StockPrice


logger = logging.getLogger(__name__)


class StockPriceCache:
    """
    Specialized cache for stock prices with 1-minute TTL
    """
    
    CACHE_TTL_SECONDS = 60  # 1 minute
    CACHE_KEY_PREFIX = "stock_price"
    
    def __init__(self, db_session: Session):
        """
        Initialize stock price cache
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.cache_manager = CacheManager(db_session)
    
    def _make_cache_key(self, symbol: str) -> str:
        """Generate cache key for stock symbol"""
        return f"{self.CACHE_KEY_PREFIX}:{symbol.upper()}"
    
    def get_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get stock price from cache
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock price data or None if not cached
        """
        cache_key = self._make_cache_key(symbol)
        cached_data = self.cache_manager.get(cache_key)
        
        if cached_data:
            logger.debug(f"Stock price cache hit: {symbol}")
            return cached_data
        
        logger.debug(f"Stock price cache miss: {symbol}")
        return None
    
    def set_price(
        self,
        symbol: str,
        price: float,
        volume: Optional[int] = None,
        open_price: Optional[float] = None,
        high_price: Optional[float] = None,
        low_price: Optional[float] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Cache stock price data
        
        Args:
            symbol: Stock symbol
            price: Current price
            volume: Trading volume
            open_price: Opening price
            high_price: High price
            low_price: Low price
            timestamp: Price timestamp
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._make_cache_key(symbol)
        
        price_data = {
            "symbol": symbol.upper(),
            "price": price,
            "volume": volume,
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "timestamp": (timestamp or datetime.now()).isoformat(),
            "cached_at": datetime.now().isoformat()
        }
        
        success = self.cache_manager.set(
            cache_key,
            price_data,
            ttl_seconds=self.CACHE_TTL_SECONDS
        )
        
        if success:
            logger.debug(f"Cached stock price: {symbol} = {price}")
        
        return success
    
    def set_price_from_model(self, stock_price: StockPrice) -> bool:
        """
        Cache stock price from StockPrice model
        
        Args:
            stock_price: StockPrice model instance
            
        Returns:
            True if successful, False otherwise
        """
        return self.set_price(
            symbol=stock_price.symbol,
            price=float(stock_price.price),
            volume=stock_price.volume,
            open_price=float(stock_price.open_price) if stock_price.open_price else None,
            high_price=float(stock_price.high_price) if stock_price.high_price else None,
            low_price=float(stock_price.low_price) if stock_price.low_price else None,
            timestamp=stock_price.timestamp
        )
    
    def invalidate_price(self, symbol: str) -> bool:
        """
        Invalidate cached price for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = self._make_cache_key(symbol)
        return self.cache_manager.delete(cache_key)
    
    def get_or_fetch(
        self,
        symbol: str,
        fetch_func: callable
    ) -> Optional[Dict[str, Any]]:
        """
        Get price from cache or fetch if not cached
        
        Args:
            symbol: Stock symbol
            fetch_func: Function to fetch price if not cached
                       Should return StockPrice model or dict
            
        Returns:
            Stock price data
        """
        # Try cache first
        cached_price = self.get_price(symbol)
        if cached_price:
            return cached_price
        
        # Fetch from source
        try:
            price_data = fetch_func(symbol)
            
            if price_data:
                # Cache the result
                if isinstance(price_data, StockPrice):
                    self.set_price_from_model(price_data)
                    return {
                        "symbol": price_data.symbol,
                        "price": float(price_data.price),
                        "volume": price_data.volume,
                        "open_price": float(price_data.open_price) if price_data.open_price else None,
                        "high_price": float(price_data.high_price) if price_data.high_price else None,
                        "low_price": float(price_data.low_price) if price_data.low_price else None,
                        "timestamp": price_data.timestamp.isoformat(),
                        "cached_at": datetime.now().isoformat()
                    }
                elif isinstance(price_data, dict):
                    self.set_price(**price_data)
                    return price_data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch price for {symbol}: {e}")
            return None
    
    def clear_all_prices(self) -> bool:
        """
        Clear all cached stock prices
        
        Returns:
            True if successful, False otherwise
        """
        return self.cache_manager.clear_all(f"{self.CACHE_KEY_PREFIX}:*")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for stock prices
        
        Returns:
            Dictionary with cache statistics
        """
        stats = self.cache_manager.get_stats()
        stats["cache_type"] = "stock_price"
        stats["ttl_seconds"] = self.CACHE_TTL_SECONDS
        return stats
