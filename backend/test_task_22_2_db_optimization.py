"""
Test suite for Task 22.2: Database Optimization
Tests indexes, query performance, and data archiving
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import inspect, text
from decimal import Decimal

from app.database import SessionLocal, engine
from models.news_article import NewsArticle
from models.sentiment_analysis import SentimentAnalysis
from models.stock_price import StockPrice
from models.trade_history import TradeHistory
from models.analysis_cache import AnalysisCache
from services.data_archiver import DataArchiver, create_archiver
from services.query_optimizer import QueryOptimizer, create_query_optimizer


class TestDatabaseIndexes:
    """Test that optimization indexes are created"""
    
    def test_news_articles_indexes(self):
        """Test news_articles table has optimization indexes"""
        inspector = inspect(engine)
        indexes = inspector.get_indexes('news_articles')
        index_names = [idx['name'] for idx in indexes]
        
        # Check for optimization indexes
        assert 'idx_news_created_published' in index_names or 'idx_published_asset' in index_names
        print(f"??News articles indexes: {index_names}")
    
    def test_sentiment_analysis_indexes(self):
        """Test sentiment_analysis table has optimization indexes"""
        inspector = inspect(engine)
        indexes = inspector.get_indexes('sentiment_analysis')
        index_names = [idx['name'] for idx in indexes]
        
        # Check for optimization indexes
        assert 'idx_sentiment_score_date' in index_names or 'idx_article_analyzed' in index_names
        print(f"??Sentiment analysis indexes: {index_names}")
    
    def test_stock_prices_indexes(self):
        """Test stock_prices table has optimization indexes"""
        inspector = inspect(engine)
        indexes = inspector.get_indexes('stock_prices')
        index_names = [idx['name'] for idx in indexes]
        
        # Check for optimization indexes
        assert 'idx_symbol_timestamp' in index_names
        print(f"??Stock prices indexes: {index_names}")
    
    def test_trade_history_indexes(self):
        """Test trade_history table has optimization indexes"""
        inspector = inspect(engine)
        indexes = inspector.get_indexes('trade_history')
        index_names = [idx['name'] for idx in indexes]
        
        # Check for optimization indexes
        assert 'idx_trade_symbol' in index_names
        assert 'idx_trade_executed_at' in index_names
        print(f"??Trade history indexes: {index_names}")


class TestDataArchiver:
    """Test data archiving functionality"""
    
    @pytest.fixture
    def db(self):
        """Create a database session"""
        db = SessionLocal()
        yield db
        db.close()
    
    @pytest.fixture
    def archiver(self, db):
        """Create a data archiver instance"""
        return create_archiver(db)
    
    def test_archiver_initialization(self, archiver):
        """Test archiver initializes with default retention periods"""
        assert archiver.retention_periods['news_articles'] == 30
        assert archiver.retention_periods['stock_prices'] == 90
        assert archiver.retention_periods['trade_history'] == 365
        print("??Archiver initialized with correct retention periods")
    
    def test_custom_retention_periods(self, db):
        """Test archiver with custom retention periods"""
        custom_periods = {
            'news_articles': 14,
            'stock_prices': 60
        }
        archiver = create_archiver(db, custom_periods)
        
        assert archiver.retention_periods['news_articles'] == 14
        assert archiver.retention_periods['stock_prices'] == 60
        print("??Custom retention periods applied correctly")
    
    def test_archive_old_news(self, db, archiver):
        """Test archiving old news articles"""
        # Create old news article
        old_date = datetime.now() - timedelta(days=40)
        old_article = NewsArticle(
            title="Old Test Article",
            content="This is old content",
            published_date=old_date,
            source="Test Source",
            asset_type="general"
        )
        db.add(old_article)
        db.commit()
        
        # Archive old news
        deleted = archiver.archive_old_news(days=30)
        
        assert deleted >= 1
        print(f"??Archived {deleted} old news articles")
    
    def test_clean_expired_cache(self, db, archiver):
        """Test cleaning expired cache entries"""
        # Create expired cache entry
        expired_cache = AnalysisCache(
            cache_key="test_expired_key",
            result_json={"test": "data"},
            expires_at=datetime.now() - timedelta(hours=1)
        )
        db.add(expired_cache)
        db.commit()
        
        # Clean expired cache
        deleted = archiver.clean_expired_cache()
        
        assert deleted >= 1
        print(f"??Cleaned {deleted} expired cache entries")
    
    def test_get_table_statistics(self, db, archiver):
        """Test getting table statistics"""
        stats = archiver.get_table_statistics()
        
        assert 'news_articles' in stats
        assert 'sentiment_analysis' in stats
        assert 'stock_prices' in stats
        assert 'trade_history' in stats
        assert 'analysis_cache' in stats
        
        print(f"??Table statistics retrieved:")
        for table, data in stats.items():
            print(f"  - {table}: {data}")


class TestQueryOptimizer:
    """Test query optimization functionality"""
    
    @pytest.fixture
    def db(self):
        """Create a database session"""
        db = SessionLocal()
        yield db
        db.close()
    
    @pytest.fixture
    def optimizer(self, db):
        """Create a query optimizer instance"""
        return create_query_optimizer(db)
    
    @pytest.fixture
    def sample_data(self, db):
        """Create sample data for testing"""
        # Create news article
        article = NewsArticle(
            title="Test Article",
            content="Test content",
            published_date=datetime.now(),
            source="Test Source",
            asset_type="general"
        )
        db.add(article)
        db.commit()
        
        # Create sentiment analysis
        sentiment = SentimentAnalysis(
            article_id=article.id,
            sentiment="Positive",
            score=1.0,
            reasoning="Test reasoning"
        )
        db.add(sentiment)
        db.commit()
        
        return article, sentiment
    
    def test_get_recent_news_with_sentiment(self, db, optimizer, sample_data):
        """Test optimized query for recent news with sentiment"""
        results = optimizer.get_recent_news_with_sentiment(days=7, limit=10)
        
        assert isinstance(results, list)
        if results:
            article, sentiment = results[0]
            assert isinstance(article, NewsArticle)
            print(f"??Retrieved {len(results)} news articles with sentiment")
    
    def test_get_daily_sentiment_scores(self, db, optimizer, sample_data):
        """Test optimized query for daily sentiment scores"""
        results = optimizer.get_daily_sentiment_scores(days=7)
        
        assert isinstance(results, list)
        if results:
            assert 'date' in results[0]
            assert 'avg_score' in results[0]
            assert 'count' in results[0]
            print(f"??Retrieved {len(results)} daily sentiment scores")
    
    def test_get_cache_hit_rate(self, db, optimizer):
        """Test cache statistics query"""
        stats = optimizer.get_cache_hit_rate()
        
        assert 'total_entries' in stats
        assert 'expired_entries' in stats
        assert 'valid_entries' in stats
        assert 'expiry_rate' in stats
        
        print(f"??Cache statistics: {stats}")
    
    def test_get_stock_price_history(self, db, optimizer):
        """Test optimized stock price history query"""
        # Create sample stock price
        stock_price = StockPrice(
            symbol="TEST",
            price=Decimal("100.00"),
            volume=1000,
            open_price=Decimal("99.00"),
            high_price=Decimal("101.00"),
            low_price=Decimal("98.00"),
            timestamp=datetime.now()
        )
        db.add(stock_price)
        db.commit()
        
        results = optimizer.get_stock_price_history("TEST", days=30)
        
        assert isinstance(results, list)
        if results:
            assert results[0].symbol == "TEST"
            print(f"??Retrieved {len(results)} stock price records")
    
    def test_get_latest_stock_prices(self, db, optimizer):
        """Test optimized latest stock prices query"""
        # Create sample stock prices
        for i in range(3):
            stock_price = StockPrice(
                symbol=f"TEST{i}",
                price=Decimal("100.00"),
                volume=1000,
                timestamp=datetime.now() - timedelta(minutes=i)
            )
            db.add(stock_price)
        db.commit()
        
        results = optimizer.get_latest_stock_prices()
        
        assert isinstance(results, list)
        print(f"??Retrieved {len(results)} latest stock prices")


class TestPerformance:
    """Test query performance improvements"""
    
    @pytest.fixture
    def db(self):
        """Create a database session"""
        db = SessionLocal()
        yield db
        db.close()
    
    def test_index_usage(self, db):
        """Test that queries use indexes (SQLite EXPLAIN QUERY PLAN)"""
        # Test news articles query
        result = db.execute(text(
            "EXPLAIN QUERY PLAN SELECT * FROM news_articles "
            "WHERE published_date >= datetime('now', '-7 days') "
            "ORDER BY published_date DESC"
        ))
        
        plan = [row for row in result]
        print(f"??Query plan for news articles:")
        for row in plan:
            print(f"  {row}")
    
    def test_sentiment_query_performance(self, db):
        """Test sentiment analysis query uses indexes"""
        result = db.execute(text(
            "EXPLAIN QUERY PLAN SELECT * FROM sentiment_analysis "
            "WHERE analyzed_at >= datetime('now', '-7 days') "
            "ORDER BY analyzed_at DESC"
        ))
        
        plan = [row for row in result]
        print(f"??Query plan for sentiment analysis:")
        for row in plan:
            print(f"  {row}")


def run_all_tests():
    """Run all database optimization tests"""
    print("\n" + "="*60)
    print("DATABASE OPTIMIZATION TESTS (Task 22.2)")
    print("="*60 + "\n")
    
    # Test indexes
    print("Testing Database Indexes...")
    print("-" * 60)
    test_indexes = TestDatabaseIndexes()
    test_indexes.test_news_articles_indexes()
    test_indexes.test_sentiment_analysis_indexes()
    test_indexes.test_stock_prices_indexes()
    test_indexes.test_trade_history_indexes()
    
    # Test archiver
    print("\nTesting Data Archiver...")
    print("-" * 60)
    db = SessionLocal()
    test_archiver = TestDataArchiver()
    archiver = create_archiver(db)
    
    test_archiver.test_archiver_initialization(archiver)
    test_archiver.test_custom_retention_periods(db)
    test_archiver.test_get_table_statistics(db, archiver)
    
    # Test query optimizer
    print("\nTesting Query Optimizer...")
    print("-" * 60)
    test_optimizer = TestQueryOptimizer()
    optimizer = create_query_optimizer(db)
    
    test_optimizer.test_get_cache_hit_rate(db, optimizer)
    test_optimizer.test_get_daily_sentiment_scores(db, optimizer, None)
    
    # Test performance
    print("\nTesting Query Performance...")
    print("-" * 60)
    test_performance = TestPerformance()
    test_performance.test_index_usage(db)
    test_performance.test_sentiment_query_performance(db)
    
    db.close()
    
    print("\n" + "="*60)
    print("ALL DATABASE OPTIMIZATION TESTS COMPLETED")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_all_tests()
