"""
Data Archiving Service
Handles archiving and cleanup of old data to maintain database performance
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, delete

try:
    from models.news_article import NewsArticle
    from models.sentiment_analysis import SentimentAnalysis
    from models.stock_price import StockPrice
    from models.trade_history import TradeHistory
    from models.analysis_cache import AnalysisCache
    from models.stock_news_relation import StockNewsRelation
except ImportError:
    from models.news_article import NewsArticle
    from models.sentiment_analysis import SentimentAnalysis
    from models.stock_price import StockPrice
    from models.trade_history import TradeHistory
    from models.analysis_cache import AnalysisCache
    from models.stock_news_relation import StockNewsRelation

logger = logging.getLogger(__name__)


class DataArchiver:
    """
    Service for archiving and cleaning up old data
    Implements retention policies for different data types
    """
    
    # Default retention periods (in days)
    DEFAULT_RETENTION_PERIODS = {
        'news_articles': 30,  # Keep news for 30 days
        'sentiment_analysis': 30,  # Keep sentiment analysis for 30 days
        'stock_prices': 90,  # Keep stock prices for 90 days
        'trade_history': 365,  # Keep trade history for 1 year
        'analysis_cache': 7,  # Keep cache for 7 days
        'stock_news_relation': 30,  # Keep relations for 30 days
    }
    
    def __init__(self, db: Session, retention_periods: Optional[Dict[str, int]] = None):
        """
        Initialize the data archiver
        
        Args:
            db: Database session
            retention_periods: Custom retention periods (in days) for each table
        """
        self.db = db
        self.retention_periods = retention_periods or self.DEFAULT_RETENTION_PERIODS
        
    def archive_old_news(self, days: Optional[int] = None) -> int:
        """
        Archive old news articles and their related data
        
        Args:
            days: Number of days to retain (default from retention_periods)
            
        Returns:
            Number of records archived/deleted
        """
        days = days or self.retention_periods['news_articles']
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # Count records to be deleted
            count = self.db.query(NewsArticle).filter(
                NewsArticle.published_date < cutoff_date
            ).count()
            
            if count == 0:
                logger.info(f"No news articles older than {days} days to archive")
                return 0
            
            # Delete old news articles (cascade will handle sentiment_analysis)
            deleted = self.db.query(NewsArticle).filter(
                NewsArticle.published_date < cutoff_date
            ).delete(synchronize_session=False)
            
            self.db.commit()
            logger.info(f"Archived {deleted} news articles older than {days} days")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error archiving news articles: {str(e)}")
            raise
    
    def archive_old_stock_prices(self, days: Optional[int] = None) -> int:
        """
        Archive old stock price data
        
        Args:
            days: Number of days to retain (default from retention_periods)
            
        Returns:
            Number of records archived/deleted
        """
        days = days or self.retention_periods['stock_prices']
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # Count records to be deleted
            count = self.db.query(StockPrice).filter(
                StockPrice.timestamp < cutoff_date
            ).count()
            
            if count == 0:
                logger.info(f"No stock prices older than {days} days to archive")
                return 0
            
            # Delete old stock prices
            deleted = self.db.query(StockPrice).filter(
                StockPrice.timestamp < cutoff_date
            ).delete(synchronize_session=False)
            
            self.db.commit()
            logger.info(f"Archived {deleted} stock price records older than {days} days")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error archiving stock prices: {str(e)}")
            raise
    
    def archive_old_trade_history(self, days: Optional[int] = None) -> int:
        """
        Archive old trade history (keep for longer period for tax/audit purposes)
        
        Args:
            days: Number of days to retain (default from retention_periods)
            
        Returns:
            Number of records archived/deleted
        """
        days = days or self.retention_periods['trade_history']
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # Count records to be deleted
            count = self.db.query(TradeHistory).filter(
                TradeHistory.executed_at < cutoff_date
            ).count()
            
            if count == 0:
                logger.info(f"No trade history older than {days} days to archive")
                return 0
            
            # Delete old trade history
            deleted = self.db.query(TradeHistory).filter(
                TradeHistory.executed_at < cutoff_date
            ).delete(synchronize_session=False)
            
            self.db.commit()
            logger.info(f"Archived {deleted} trade history records older than {days} days")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error archiving trade history: {str(e)}")
            raise
    
    def clean_expired_cache(self) -> int:
        """
        Clean up expired cache entries
        
        Returns:
            Number of cache entries deleted
        """
        try:
            # Delete expired cache entries
            deleted = self.db.query(AnalysisCache).filter(
                AnalysisCache.expires_at < datetime.now()
            ).delete(synchronize_session=False)
            
            self.db.commit()
            logger.info(f"Cleaned {deleted} expired cache entries")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning expired cache: {str(e)}")
            raise
    
    def clean_old_cache(self, days: Optional[int] = None) -> int:
        """
        Clean up old cache entries regardless of expiry
        
        Args:
            days: Number of days to retain (default from retention_periods)
            
        Returns:
            Number of cache entries deleted
        """
        days = days or self.retention_periods['analysis_cache']
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # Delete old cache entries
            deleted = self.db.query(AnalysisCache).filter(
                AnalysisCache.created_at < cutoff_date
            ).delete(synchronize_session=False)
            
            self.db.commit()
            logger.info(f"Cleaned {deleted} cache entries older than {days} days")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning old cache: {str(e)}")
            raise
    
    def archive_old_stock_news_relations(self, days: Optional[int] = None) -> int:
        """
        Archive old stock-news relations
        
        Args:
            days: Number of days to retain (default from retention_periods)
            
        Returns:
            Number of records archived/deleted
        """
        days = days or self.retention_periods['stock_news_relation']
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # Delete relations for old news articles
            deleted = self.db.query(StockNewsRelation).filter(
                StockNewsRelation.article_id.in_(
                    self.db.query(NewsArticle.id).filter(
                        NewsArticle.published_date < cutoff_date
                    )
                )
            ).delete(synchronize_session=False)
            
            self.db.commit()
            logger.info(f"Archived {deleted} stock-news relations older than {days} days")
            return deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error archiving stock-news relations: {str(e)}")
            raise
    
    def archive_all(self) -> Dict[str, int]:
        """
        Run all archiving operations
        
        Returns:
            Dictionary with counts of archived records per table
        """
        results = {}
        
        try:
            # Archive in order (relations first, then main tables)
            results['expired_cache'] = self.clean_expired_cache()
            results['old_cache'] = self.clean_old_cache()
            results['stock_news_relations'] = self.archive_old_stock_news_relations()
            results['news_articles'] = self.archive_old_news()
            results['stock_prices'] = self.archive_old_stock_prices()
            results['trade_history'] = self.archive_old_trade_history()
            
            total = sum(results.values())
            logger.info(f"Archiving complete. Total records archived: {total}")
            logger.info(f"Breakdown: {results}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error during archiving: {str(e)}")
            raise
    
    def get_table_statistics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics about table sizes and oldest records
        
        Returns:
            Dictionary with statistics per table
        """
        stats = {}
        
        try:
            # News articles stats
            news_count = self.db.query(func.count(NewsArticle.id)).scalar()
            oldest_news = self.db.query(func.min(NewsArticle.published_date)).scalar()
            stats['news_articles'] = {
                'count': news_count,
                'oldest_record': oldest_news.isoformat() if oldest_news else None
            }
            
            # Sentiment analysis stats
            sentiment_count = self.db.query(func.count(SentimentAnalysis.id)).scalar()
            oldest_sentiment = self.db.query(func.min(SentimentAnalysis.analyzed_at)).scalar()
            stats['sentiment_analysis'] = {
                'count': sentiment_count,
                'oldest_record': oldest_sentiment.isoformat() if oldest_sentiment else None
            }
            
            # Stock prices stats
            stock_count = self.db.query(func.count(StockPrice.id)).scalar()
            oldest_stock = self.db.query(func.min(StockPrice.timestamp)).scalar()
            stats['stock_prices'] = {
                'count': stock_count,
                'oldest_record': oldest_stock.isoformat() if oldest_stock else None
            }
            
            # Trade history stats
            trade_count = self.db.query(func.count(TradeHistory.id)).scalar()
            oldest_trade = self.db.query(func.min(TradeHistory.executed_at)).scalar()
            stats['trade_history'] = {
                'count': trade_count,
                'oldest_record': oldest_trade.isoformat() if oldest_trade else None
            }
            
            # Cache stats
            cache_count = self.db.query(func.count(AnalysisCache.id)).scalar()
            expired_cache = self.db.query(func.count(AnalysisCache.id)).filter(
                AnalysisCache.expires_at < datetime.now()
            ).scalar()
            stats['analysis_cache'] = {
                'count': cache_count,
                'expired_count': expired_cache
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting table statistics: {str(e)}")
            raise


def create_archiver(db: Session, retention_periods: Optional[Dict[str, int]] = None) -> DataArchiver:
    """
    Factory function to create a DataArchiver instance
    
    Args:
        db: Database session
        retention_periods: Custom retention periods
        
    Returns:
        DataArchiver instance
    """
    return DataArchiver(db, retention_periods)
