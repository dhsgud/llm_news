"""
Query Optimizer Service
Provides optimized database queries for common operations
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, case
from decimal import Decimal

try:
    from models.news_article import NewsArticle
    from models.sentiment_analysis import SentimentAnalysis
    from models.stock_price import StockPrice
    from models.trade_history import TradeHistory
    from models.analysis_cache import AnalysisCache
    from models.stock_news_relation import StockNewsRelation
    from models.account_holding import AccountHolding
except ImportError:
    from models.news_article import NewsArticle
    from models.sentiment_analysis import SentimentAnalysis
    from models.stock_price import StockPrice
    from models.trade_history import TradeHistory
    from models.analysis_cache import AnalysisCache
    from models.stock_news_relation import StockNewsRelation
    from models.account_holding import AccountHolding

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Provides optimized queries for common database operations
    Uses proper indexing and query patterns for performance
    """
    
    def __init__(self, db: Session):
        """
        Initialize the query optimizer
        
        Args:
            db: Database session
        """
        self.db = db
    
    def get_recent_news_with_sentiment(
        self,
        days: int = 7,
        asset_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Tuple[NewsArticle, Optional[SentimentAnalysis]]]:
        """
        Optimized query to get recent news with their sentiment analysis
        Uses composite index on published_date and asset_type
        
        Args:
            days: Number of days to look back
            asset_type: Filter by asset type
            limit: Maximum number of results
            
        Returns:
            List of (NewsArticle, SentimentAnalysis) tuples
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = self.db.query(NewsArticle, SentimentAnalysis).outerjoin(
            SentimentAnalysis,
            NewsArticle.id == SentimentAnalysis.article_id
        ).filter(
            NewsArticle.published_date >= cutoff_date
        )
        
        if asset_type:
            query = query.filter(NewsArticle.asset_type == asset_type)
        
        # Order by published_date descending (uses index)
        query = query.order_by(desc(NewsArticle.published_date))
        
        return query.limit(limit).all()
    
    def get_daily_sentiment_scores(
        self,
        days: int = 7,
        asset_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Optimized query to get daily aggregated sentiment scores
        Uses indexes on analyzed_at and sentiment
        
        Args:
            days: Number of days to aggregate
            asset_type: Filter by asset type
            
        Returns:
            List of daily sentiment aggregates
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Build base query with join
        query = self.db.query(
            func.date(SentimentAnalysis.analyzed_at).label('date'),
            func.avg(SentimentAnalysis.score).label('avg_score'),
            func.count(SentimentAnalysis.id).label('count'),
            func.sum(
                case(
                    (SentimentAnalysis.sentiment == 'Positive', 1),
                    else_=0
                )
            ).label('positive_count'),
            func.sum(
                case(
                    (SentimentAnalysis.sentiment == 'Negative', 1),
                    else_=0
                )
            ).label('negative_count'),
            func.sum(
                case(
                    (SentimentAnalysis.sentiment == 'Neutral', 1),
                    else_=0
                )
            ).label('neutral_count')
        ).filter(
            SentimentAnalysis.analyzed_at >= cutoff_date
        )
        
        # Add asset type filter if specified
        if asset_type:
            query = query.join(
                NewsArticle,
                SentimentAnalysis.article_id == NewsArticle.id
            ).filter(
                NewsArticle.asset_type == asset_type
            )
        
        # Group by date and order
        query = query.group_by(func.date(SentimentAnalysis.analyzed_at))
        query = query.order_by(asc(func.date(SentimentAnalysis.analyzed_at)))
        
        results = query.all()
        
        return [
            {
                'date': r.date.isoformat(),
                'avg_score': float(r.avg_score) if r.avg_score else 0.0,
                'count': r.count,
                'positive_count': r.positive_count,
                'negative_count': r.negative_count,
                'neutral_count': r.neutral_count
            }
            for r in results
        ]
    
    def get_stock_price_history(
        self,
        symbol: str,
        days: int = 30,
        limit: int = 1000
    ) -> List[StockPrice]:
        """
        Optimized query to get stock price history
        Uses composite index on symbol and timestamp
        
        Args:
            symbol: Stock symbol
            days: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of StockPrice records
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.db.query(StockPrice).filter(
            and_(
                StockPrice.symbol == symbol,
                StockPrice.timestamp >= cutoff_date
            )
        ).order_by(desc(StockPrice.timestamp)).limit(limit).all()
    
    def get_latest_stock_prices(
        self,
        symbols: Optional[List[str]] = None
    ) -> List[StockPrice]:
        """
        Optimized query to get latest price for each symbol
        Uses subquery with index on symbol and timestamp
        
        Args:
            symbols: List of symbols to query (None for all)
            
        Returns:
            List of latest StockPrice records
        """
        # Subquery to get latest timestamp per symbol
        subquery = self.db.query(
            StockPrice.symbol,
            func.max(StockPrice.timestamp).label('max_timestamp')
        ).group_by(StockPrice.symbol)
        
        if symbols:
            subquery = subquery.filter(StockPrice.symbol.in_(symbols))
        
        subquery = subquery.subquery()
        
        # Join to get full records
        query = self.db.query(StockPrice).join(
            subquery,
            and_(
                StockPrice.symbol == subquery.c.symbol,
                StockPrice.timestamp == subquery.c.max_timestamp
            )
        )
        
        return query.all()
    
    def get_trade_performance_summary(
        self,
        user_id: str,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Optimized query to get trade performance summary
        Uses indexes on user_id and executed_at
        
        Args:
            user_id: User identifier
            days: Number of days to analyze (None for all time)
            
        Returns:
            Performance summary dictionary
        """
        query = self.db.query(
            func.count(TradeHistory.id).label('total_trades'),
            func.sum(
                case(
                    (TradeHistory.trade_type == 'BUY', 1),
                    else_=0
                )
            ).label('buy_count'),
            func.sum(
                case(
                    (TradeHistory.trade_type == 'SELL', 1),
                    else_=0
                )
            ).label('sell_count'),
            func.sum(TradeHistory.profit_loss).label('total_profit_loss'),
            func.avg(TradeHistory.profit_loss).label('avg_profit_loss'),
            func.sum(TradeHistory.total_amount).label('total_volume')
        ).filter(
            TradeHistory.user_id == user_id
        )
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            query = query.filter(TradeHistory.executed_at >= cutoff_date)
        
        result = query.first()
        
        return {
            'total_trades': result.total_trades or 0,
            'buy_count': result.buy_count or 0,
            'sell_count': result.sell_count or 0,
            'total_profit_loss': float(result.total_profit_loss) if result.total_profit_loss else 0.0,
            'avg_profit_loss': float(result.avg_profit_loss) if result.avg_profit_loss else 0.0,
            'total_volume': float(result.total_volume) if result.total_volume else 0.0
        }
    
    def get_top_performing_stocks(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Optimized query to get top performing stocks by profit/loss
        Uses indexes on user_id and symbol
        
        Args:
            user_id: User identifier
            limit: Number of top stocks to return
            
        Returns:
            List of stock performance dictionaries
        """
        results = self.db.query(
            TradeHistory.symbol,
            func.sum(TradeHistory.profit_loss).label('total_profit_loss'),
            func.count(TradeHistory.id).label('trade_count'),
            func.avg(TradeHistory.signal_ratio).label('avg_signal_ratio')
        ).filter(
            TradeHistory.user_id == user_id
        ).group_by(
            TradeHistory.symbol
        ).order_by(
            desc(func.sum(TradeHistory.profit_loss))
        ).limit(limit).all()
        
        return [
            {
                'symbol': r.symbol,
                'total_profit_loss': float(r.total_profit_loss) if r.total_profit_loss else 0.0,
                'trade_count': r.trade_count,
                'avg_signal_ratio': float(r.avg_signal_ratio) if r.avg_signal_ratio else None
            }
            for r in results
        ]
    
    def get_stock_sentiment_summary(
        self,
        symbol: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Optimized query to get sentiment summary for a specific stock
        Uses indexes on stock_symbol and article_id
        
        Args:
            symbol: Stock symbol
            days: Number of days to analyze
            
        Returns:
            Sentiment summary dictionary
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        result = self.db.query(
            func.count(SentimentAnalysis.id).label('total_articles'),
            func.avg(SentimentAnalysis.score).label('avg_score'),
            func.sum(
                case(
                    (SentimentAnalysis.sentiment == 'Positive', 1),
                    else_=0
                )
            ).label('positive_count'),
            func.sum(
                case(
                    (SentimentAnalysis.sentiment == 'Negative', 1),
                    else_=0
                )
            ).label('negative_count'),
            func.sum(
                case(
                    (SentimentAnalysis.sentiment == 'Neutral', 1),
                    else_=0
                )
            ).label('neutral_count')
        ).join(
            StockNewsRelation,
            SentimentAnalysis.article_id == StockNewsRelation.article_id
        ).filter(
            and_(
                StockNewsRelation.stock_symbol == symbol,
                SentimentAnalysis.analyzed_at >= cutoff_date
            )
        ).first()
        
        return {
            'symbol': symbol,
            'total_articles': result.total_articles or 0,
            'avg_score': float(result.avg_score) if result.avg_score else 0.0,
            'positive_count': result.positive_count or 0,
            'negative_count': result.negative_count or 0,
            'neutral_count': result.neutral_count or 0
        }
    
    def get_cache_hit_rate(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics dictionary
        """
        total = self.db.query(func.count(AnalysisCache.id)).scalar()
        expired = self.db.query(func.count(AnalysisCache.id)).filter(
            AnalysisCache.expires_at < datetime.now()
        ).scalar()
        
        return {
            'total_entries': total or 0,
            'expired_entries': expired or 0,
            'valid_entries': (total or 0) - (expired or 0),
            'expiry_rate': (expired / total * 100) if total else 0.0
        }
    
    def vacuum_analyze_tables(self) -> None:
        """
        Run VACUUM ANALYZE on all tables (PostgreSQL only)
        This updates statistics and reclaims space
        
        Note: This is a maintenance operation and should be run during low-traffic periods
        """
        try:
            # Check if we're using PostgreSQL
            if 'postgresql' in str(self.db.bind.url):
                tables = [
                    'news_articles',
                    'sentiment_analysis',
                    'stock_prices',
                    'trade_history',
                    'analysis_cache',
                    'stock_news_relation',
                    'account_holdings',
                    'auto_trade_config'
                ]
                
                for table in tables:
                    try:
                        self.db.execute(f"VACUUM ANALYZE {table}")
                        logger.info(f"VACUUM ANALYZE completed for {table}")
                    except Exception as e:
                        logger.warning(f"Could not VACUUM ANALYZE {table}: {str(e)}")
                
                self.db.commit()
            else:
                logger.info("VACUUM ANALYZE is only supported for PostgreSQL")
                
        except Exception as e:
            logger.error(f"Error during VACUUM ANALYZE: {str(e)}")
            self.db.rollback()


def create_query_optimizer(db: Session) -> QueryOptimizer:
    """
    Factory function to create a QueryOptimizer instance
    
    Args:
        db: Database session
        
    Returns:
        QueryOptimizer instance
    """
    return QueryOptimizer(db)
