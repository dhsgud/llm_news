"""
Test script to verify database setup
Run this to ensure database connection and models are working correctly
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import init_db, get_db, engine
from models import NewsArticle, SentimentAnalysis, AnalysisCache
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_setup():
    """Test database initialization and basic operations"""
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        logger.info("??Database initialized successfully")
        
        # Test database connection
        logger.info("Testing database connection...")
        db = next(get_db())
        
        # Test creating a news article
        logger.info("Testing NewsArticle model...")
        test_article = NewsArticle(
            title="Test Article",
            content="This is a test article content",
            published_date=datetime.now(),
            source="Test Source",
            url="https://example.com/test",
            asset_type="general"
        )
        db.add(test_article)
        db.commit()
        db.refresh(test_article)
        logger.info(f"??Created NewsArticle with ID: {test_article.id}")
        
        # Test creating a sentiment analysis
        logger.info("Testing SentimentAnalysis model...")
        test_sentiment = SentimentAnalysis(
            article_id=test_article.id,
            sentiment="Positive",
            score=1.0,
            reasoning="Test reasoning"
        )
        db.add(test_sentiment)
        db.commit()
        db.refresh(test_sentiment)
        logger.info(f"??Created SentimentAnalysis with ID: {test_sentiment.id}")
        
        # Test creating a cache entry
        logger.info("Testing AnalysisCache model...")
        test_cache = AnalysisCache(
            cache_key="test_key",
            result_json={"test": "data", "value": 123},
            expires_at=datetime.now() + timedelta(hours=1)
        )
        db.add(test_cache)
        db.commit()
        db.refresh(test_cache)
        logger.info(f"??Created AnalysisCache with ID: {test_cache.id}")
        
        # Test querying
        logger.info("Testing queries...")
        articles = db.query(NewsArticle).all()
        logger.info(f"??Found {len(articles)} article(s)")
        
        sentiments = db.query(SentimentAnalysis).all()
        logger.info(f"??Found {len(sentiments)} sentiment analysis(es)")
        
        caches = db.query(AnalysisCache).all()
        logger.info(f"??Found {len(caches)} cache entry(ies)")
        
        # Clean up test data
        logger.info("Cleaning up test data...")
        db.delete(test_sentiment)
        db.delete(test_cache)
        db.delete(test_article)
        db.commit()
        logger.info("??Test data cleaned up")
        
        db.close()
        
        logger.info("\n" + "="*50)
        logger.info("??All database tests passed successfully!")
        logger.info("="*50)
        
        return True
        
    except Exception as e:
        logger.error(f"??Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_database_setup()
    sys.exit(0 if success else 1)
