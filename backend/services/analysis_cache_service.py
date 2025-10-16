"""
Analysis Result Caching Service
Implements 1-hour caching for analysis results to reduce LLM calls
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

try:
    from services.cache_manager import CacheManager
    from config import settings
except ImportError:
    from services.cache_manager import CacheManager
    from config import settings


logger = logging.getLogger(__name__)


class AnalysisCacheService:
    """
    Specialized cache for analysis results with 1-hour TTL
    """
    
    CACHE_TTL_HOURS = 1  # 1 hour
    
    # Cache key prefixes for different analysis types
    KEY_MARKET_ANALYSIS = "analysis:market"
    KEY_STOCK_SENTIMENT = "analysis:stock_sentiment"
    KEY_TREND_SUMMARY = "analysis:trend_summary"
    KEY_RECOMMENDATION = "analysis:recommendation"
    KEY_DAILY_SENTIMENT = "analysis:daily_sentiment"
    
    def __init__(self, db_session: Session):
        """
        Initialize analysis cache service
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.cache_manager = CacheManager(db_session)
    
    def get_market_analysis(self, asset_type: str = "general") -> Optional[Dict[str, Any]]:
        """
        Get cached market analysis result
        
        Args:
            asset_type: Type of asset (general, stock, crypto)
            
        Returns:
            Cached analysis result or None
        """
        cache_key = f"{self.KEY_MARKET_ANALYSIS}:{asset_type}"
        result = self.cache_manager.get(cache_key)
        
        if result:
            logger.info(f"Market analysis cache hit: {asset_type}")
        else:
            logger.info(f"Market analysis cache miss: {asset_type}")
        
        return result
    
    def set_market_analysis(
        self,
        asset_type: str,
        buy_sell_ratio: int,
        trend_summary: str,
        vix: float,
        confidence: str = "medium"
    ) -> bool:
        """
        Cache market analysis result
        
        Args:
            asset_type: Type of asset
            buy_sell_ratio: Buy/sell ratio (0-100)
            trend_summary: Trend summary text
            vix: VIX value
            confidence: Confidence level
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = f"{self.KEY_MARKET_ANALYSIS}:{asset_type}"
        
        analysis_data = {
            "buy_sell_ratio": buy_sell_ratio,
            "trend_summary": trend_summary,
            "vix": vix,
            "confidence": confidence,
            "last_updated": datetime.now().isoformat(),
            "asset_type": asset_type
        }
        
        success = self.cache_manager.set(
            cache_key,
            analysis_data,
            ttl_hours=self.CACHE_TTL_HOURS
        )
        
        if success:
            logger.info(f"Cached market analysis: {asset_type}")
        
        return success
    
    def get_stock_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached stock sentiment analysis
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Cached sentiment result or None
        """
        cache_key = f"{self.KEY_STOCK_SENTIMENT}:{symbol.upper()}"
        result = self.cache_manager.get(cache_key)
        
        if result:
            logger.debug(f"Stock sentiment cache hit: {symbol}")
        else:
            logger.debug(f"Stock sentiment cache miss: {symbol}")
        
        return result
    
    def set_stock_sentiment(
        self,
        symbol: str,
        sentiment: str,
        score: float,
        reasoning: str,
        related_news_count: int = 0
    ) -> bool:
        """
        Cache stock sentiment analysis
        
        Args:
            symbol: Stock symbol
            sentiment: Sentiment (Positive, Negative, Neutral)
            score: Sentiment score
            reasoning: Analysis reasoning
            related_news_count: Number of related news articles
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = f"{self.KEY_STOCK_SENTIMENT}:{symbol.upper()}"
        
        sentiment_data = {
            "symbol": symbol.upper(),
            "sentiment": sentiment,
            "score": score,
            "reasoning": reasoning,
            "related_news_count": related_news_count,
            "analyzed_at": datetime.now().isoformat()
        }
        
        success = self.cache_manager.set(
            cache_key,
            sentiment_data,
            ttl_hours=self.CACHE_TTL_HOURS
        )
        
        if success:
            logger.debug(f"Cached stock sentiment: {symbol}")
        
        return success
    
    def get_trend_summary(self, days: int = 7) -> Optional[Dict[str, Any]]:
        """
        Get cached trend summary
        
        Args:
            days: Number of days for trend analysis
            
        Returns:
            Cached trend summary or None
        """
        cache_key = f"{self.KEY_TREND_SUMMARY}:{days}d"
        result = self.cache_manager.get(cache_key)
        
        if result:
            logger.info(f"Trend summary cache hit: {days} days")
        else:
            logger.info(f"Trend summary cache miss: {days} days")
        
        return result
    
    def set_trend_summary(
        self,
        summary_text: str,
        dominant_sentiment: str,
        key_drivers: List[str],
        days: int = 7
    ) -> bool:
        """
        Cache trend summary
        
        Args:
            summary_text: Summary text
            dominant_sentiment: Dominant sentiment
            key_drivers: List of key drivers
            days: Number of days analyzed
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = f"{self.KEY_TREND_SUMMARY}:{days}d"
        
        trend_data = {
            "summary_text": summary_text,
            "dominant_sentiment": dominant_sentiment,
            "key_drivers": key_drivers,
            "days": days,
            "generated_at": datetime.now().isoformat()
        }
        
        success = self.cache_manager.set(
            cache_key,
            trend_data,
            ttl_hours=self.CACHE_TTL_HOURS
        )
        
        if success:
            logger.info(f"Cached trend summary: {days} days")
        
        return success
    
    def get_daily_sentiment(self, days: int = 7) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached daily sentiment scores
        
        Args:
            days: Number of days
            
        Returns:
            List of daily sentiment data or None
        """
        cache_key = f"{self.KEY_DAILY_SENTIMENT}:{days}d"
        result = self.cache_manager.get(cache_key)
        
        if result:
            logger.debug(f"Daily sentiment cache hit: {days} days")
        else:
            logger.debug(f"Daily sentiment cache miss: {days} days")
        
        return result
    
    def set_daily_sentiment(
        self,
        daily_scores: List[Dict[str, Any]],
        days: int = 7
    ) -> bool:
        """
        Cache daily sentiment scores
        
        Args:
            daily_scores: List of daily sentiment data
            days: Number of days
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = f"{self.KEY_DAILY_SENTIMENT}:{days}d"
        
        data = {
            "daily_scores": daily_scores,
            "days": days,
            "cached_at": datetime.now().isoformat()
        }
        
        success = self.cache_manager.set(
            cache_key,
            data,
            ttl_hours=self.CACHE_TTL_HOURS
        )
        
        if success:
            logger.debug(f"Cached daily sentiment: {days} days")
        
        return success
    
    def invalidate_market_analysis(self, asset_type: str = "general") -> bool:
        """
        Invalidate market analysis cache
        
        Args:
            asset_type: Type of asset
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = f"{self.KEY_MARKET_ANALYSIS}:{asset_type}"
        return self.cache_manager.delete(cache_key)
    
    def invalidate_stock_sentiment(self, symbol: str) -> bool:
        """
        Invalidate stock sentiment cache
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if successful, False otherwise
        """
        cache_key = f"{self.KEY_STOCK_SENTIMENT}:{symbol.upper()}"
        return self.cache_manager.delete(cache_key)
    
    def invalidate_all_analysis(self) -> bool:
        """
        Invalidate all analysis caches
        
        Returns:
            True if successful, False otherwise
        """
        return self.cache_manager.clear_all("analysis:*")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for analysis results
        
        Returns:
            Dictionary with cache statistics
        """
        stats = self.cache_manager.get_stats()
        stats["cache_type"] = "analysis"
        stats["ttl_hours"] = self.CACHE_TTL_HOURS
        return stats
