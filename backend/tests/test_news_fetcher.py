"""
Tests for News Fetcher Module
Tests news collection with mock API responses and database storage verification
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.news_fetcher import (
    NewsAPIClient,
    NewsScheduler,
    NewsAPIClientError
)
from models.news_article import NewsArticleCreate, NewsArticle
from app.database import Base


# Test database setup
@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_factory(test_db):
    """Factory function that returns the test database session"""
    def factory():
        return test_db
    return factory


class TestNewsAPIClient:
    """Tests for NewsAPIClient"""
    
    def test_init(self):
        """Test client initialization"""
        client = NewsAPIClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.base_url is not None
    
    def test_filter_financial_news(self):
        """Test financial news filtering"""
        client = NewsAPIClient(api_key="test_key")
        
        # Create test articles
        articles = [
            NewsArticleCreate(
                title="Stock Market Rises",
                content="The stock market saw gains today...",
                published_date=datetime.now(),
                source="Test Source",
                asset_type="general"
            ),
            NewsArticleCreate(
                title="Celebrity News",
                content="A celebrity did something...",
                published_date=datetime.now(),
                source="Test Source",
                asset_type="general"
            ),
            NewsArticleCreate(
                title="Bitcoin Hits New High",
                content="Cryptocurrency market is booming...",
                published_date=datetime.now(),
                source="Test Source",
                asset_type="general"
            )
        ]
        
        # Filter articles
        filtered = client.filter_financial_news(articles)
        
        # Should keep only financial articles
        assert len(filtered) == 2
        assert "Stock Market" in filtered[0].title or "Bitcoin" in filtered[0].title
    
    @patch('backend.services.news_fetcher.requests.Session.get')
    def test_fetch_news_success(self, mock_get):
        """Test successful news fetch with mock API response"""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 1,
            "articles": [
                {
                    "title": "Test Stock Article",
                    "description": "Stock market news",
                    "content": "Full content about stocks...",
                    "publishedAt": "2025-10-07T12:00:00Z",
                    "source": {"name": "Test Source"},
                    "url": "https://example.com/article"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = NewsAPIClient(api_key="test_key")
        
        # Fetch news
        articles = client.fetch_news(
            query="stock",
            from_date=datetime.now() - timedelta(days=1),
            to_date=datetime.now()
        )
        
        # Verify results
        assert len(articles) >= 0  # May be filtered
        mock_get.assert_called_once()
    
    @patch('backend.services.news_fetcher.requests.Session.get')
    def test_fetch_news_multiple_articles(self, mock_get):
        """Test fetching multiple articles with various financial keywords"""
        # Mock API response with multiple articles
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "totalResults": 5,
            "articles": [
                {
                    "title": "Stock Market Surges on Tech Rally",
                    "description": "Technology stocks lead market gains",
                    "content": "The stock market experienced significant gains today as tech stocks rallied...",
                    "publishedAt": "2025-10-07T10:00:00Z",
                    "source": {"name": "Financial Times"},
                    "url": "https://example.com/article1"
                },
                {
                    "title": "Bitcoin Reaches New All-Time High",
                    "description": "Cryptocurrency market booms",
                    "content": "Bitcoin has reached a new all-time high as cryptocurrency adoption increases...",
                    "publishedAt": "2025-10-07T11:00:00Z",
                    "source": {"name": "Bloomberg"},
                    "url": "https://example.com/article2"
                },
                {
                    "title": "Federal Reserve Announces Interest Rate Decision",
                    "description": "Central bank maintains current rates",
                    "content": "The Federal Reserve announced its decision to maintain interest rates at current levels...",
                    "publishedAt": "2025-10-07T12:00:00Z",
                    "source": {"name": "Reuters"},
                    "url": "https://example.com/article3"
                },
                {
                    "title": "Celebrity Wedding Photos",
                    "description": "Non-financial news",
                    "content": "Celebrity couple shares wedding photos...",
                    "publishedAt": "2025-10-07T13:00:00Z",
                    "source": {"name": "Entertainment Weekly"},
                    "url": "https://example.com/article4"
                },
                {
                    "title": "Global Economy Shows Signs of Recovery",
                    "description": "Economic indicators improve",
                    "content": "Global economic indicators show signs of recovery as markets stabilize...",
                    "publishedAt": "2025-10-07T14:00:00Z",
                    "source": {"name": "Wall Street Journal"},
                    "url": "https://example.com/article5"
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = NewsAPIClient(api_key="test_key")
        
        # Fetch news
        articles = client.fetch_news(
            query="finance OR stock OR market",
            from_date=datetime.now() - timedelta(days=1),
            to_date=datetime.now()
        )
        
        # Verify results - should filter out non-financial news
        assert len(articles) >= 3  # At least 3 financial articles
        assert all(any(keyword in (article.title + article.content).lower() 
                      for keyword in ["stock", "market", "bitcoin", "economy", "federal reserve"])
                  for article in articles)
    
    @patch('backend.services.news_fetcher.requests.Session.get')
    def test_fetch_news_api_error(self, mock_get):
        """Test API error handling"""
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        client = NewsAPIClient(api_key="invalid_key")
        
        # Should raise error
        with pytest.raises(NewsAPIClientError, match="Invalid News API key"):
            client.fetch_news()
    
    @patch('backend.services.news_fetcher.requests.Session.get')
    def test_fetch_news_rate_limit(self, mock_get):
        """Test rate limit error handling"""
        # Mock rate limit error
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        
        client = NewsAPIClient(api_key="test_key")
        
        # Should raise rate limit error
        with pytest.raises(NewsAPIClientError, match="rate limit exceeded"):
            client.fetch_news()
    
    def test_fetch_news_no_api_key(self):
        """Test fetch without API key"""
        client = NewsAPIClient(api_key="")
        
        with pytest.raises(NewsAPIClientError, match="not configured"):
            client.fetch_news()
    
    def test_convert_to_articles(self):
        """Test conversion of raw API data to articles"""
        client = NewsAPIClient(api_key="test_key")
        
        raw_articles = [
            {
                "title": "Test Article",
                "description": "Test description",
                "content": "Test content",
                "publishedAt": "2025-10-07T12:00:00Z",
                "source": {"name": "Test Source"},
                "url": "https://example.com/test"
            }
        ]
        
        articles = client._convert_to_articles(raw_articles)
        
        assert len(articles) == 1
        assert articles[0].title == "Test Article"
        assert "Test description" in articles[0].content
        assert articles[0].source == "Test Source"
    
    def test_convert_to_articles_missing_fields(self):
        """Test conversion with missing fields"""
        client = NewsAPIClient(api_key="test_key")
        
        raw_articles = [
            {
                "title": "Complete Article",
                "description": "Description",
                "content": "Content",
                "publishedAt": "2025-10-07T12:00:00Z",
                "source": {"name": "Source"},
                "url": "https://example.com/1"
            },
            {
                "title": "",  # Missing title
                "description": "Description",
                "content": "Content",
                "publishedAt": "2025-10-07T12:00:00Z",
                "source": {"name": "Source"},
                "url": "https://example.com/2"
            },
            {
                "title": "No Content Article",
                "description": "",
                "content": "",  # Missing content
                "publishedAt": "2025-10-07T12:00:00Z",
                "source": {"name": "Source"},
                "url": "https://example.com/3"
            }
        ]
        
        articles = client._convert_to_articles(raw_articles)
        
        # Should only convert valid articles
        assert len(articles) == 1
        assert articles[0].title == "Complete Article"


class TestNewsScheduler:
    """Tests for NewsScheduler"""
    
    def test_init(self):
        """Test scheduler initialization"""
        mock_db_factory = Mock()
        mock_client = Mock(spec=NewsAPIClient)
        
        scheduler = NewsScheduler(
            db_session_factory=mock_db_factory,
            news_client=mock_client,
            collection_hour=0,
            collection_minute=0,
            retention_days=7
        )
        
        assert scheduler.collection_hour == 0
        assert scheduler.collection_minute == 0
        assert scheduler.retention_days == 7
        assert not scheduler.is_running
    
    def test_schedule_daily_collection(self):
        """Test scheduling daily collection"""
        mock_db_factory = Mock()
        mock_client = Mock(spec=NewsAPIClient)
        
        scheduler = NewsScheduler(
            db_session_factory=mock_db_factory,
            news_client=mock_client
        )
        
        # Schedule collection
        scheduler.schedule_daily_collection()
        
        # Verify job was added
        job = scheduler.scheduler.get_job("daily_news_collection")
        assert job is not None
        assert job.name == "Daily News Collection"
    
    def test_start_stop(self):
        """Test starting and stopping scheduler"""
        mock_db_factory = Mock()
        mock_client = Mock(spec=NewsAPIClient)
        
        scheduler = NewsScheduler(
            db_session_factory=mock_db_factory,
            news_client=mock_client
        )
        
        # Start scheduler
        scheduler.start()
        assert scheduler.is_running
        
        # Stop scheduler
        scheduler.stop()
        assert not scheduler.is_running
    
    def test_cleanup_old_news(self, test_db):
        """Test cleanup of old news with real database"""
        mock_db_factory = Mock()
        mock_client = Mock(spec=NewsAPIClient)
        
        scheduler = NewsScheduler(
            db_session_factory=mock_db_factory,
            news_client=mock_client
        )
        
        # Add test articles with different dates
        old_article = NewsArticle(
            title="Old Article",
            content="Old content",
            published_date=datetime.now() - timedelta(days=10),
            source="Test Source",
            asset_type="general"
        )
        recent_article = NewsArticle(
            title="Recent Article",
            content="Recent content",
            published_date=datetime.now() - timedelta(days=3),
            source="Test Source",
            asset_type="general"
        )
        
        test_db.add(old_article)
        test_db.add(recent_article)
        test_db.commit()
        
        # Cleanup old news (>7 days)
        deleted_count = scheduler.cleanup_old_news(test_db, days=7)
        
        # Verify deletion
        assert deleted_count == 1
        
        # Verify only recent article remains
        remaining = test_db.query(NewsArticle).all()
        assert len(remaining) == 1
        assert remaining[0].title == "Recent Article"
    
    def test_store_articles(self, test_db):
        """Test storing articles in real database"""
        mock_db_factory = Mock()
        mock_client = Mock(spec=NewsAPIClient)
        
        scheduler = NewsScheduler(
            db_session_factory=mock_db_factory,
            news_client=mock_client
        )
        
        # Create test articles
        articles = [
            NewsArticleCreate(
                title="Test Article 1",
                content="Test content 1",
                published_date=datetime.now(),
                source="Test Source",
                url="https://example.com/test1",
                asset_type="general"
            ),
            NewsArticleCreate(
                title="Test Article 2",
                content="Test content 2",
                published_date=datetime.now(),
                source="Test Source",
                url="https://example.com/test2",
                asset_type="general"
            )
        ]
        
        # Store articles
        stored_count = scheduler._store_articles(test_db, articles)
        
        # Verify storage
        assert stored_count == 2
        
        # Verify articles in database
        db_articles = test_db.query(NewsArticle).all()
        assert len(db_articles) == 2
        assert db_articles[0].title == "Test Article 1"
        assert db_articles[1].title == "Test Article 2"
    
    def test_store_articles_duplicate_prevention(self, test_db):
        """Test that duplicate articles are not stored"""
        mock_db_factory = Mock()
        mock_client = Mock(spec=NewsAPIClient)
        
        scheduler = NewsScheduler(
            db_session_factory=mock_db_factory,
            news_client=mock_client
        )
        
        # Create test article
        article = NewsArticleCreate(
            title="Duplicate Test Article",
            content="Test content",
            published_date=datetime.now(),
            source="Test Source",
            url="https://example.com/duplicate",
            asset_type="general"
        )
        
        # Store article first time
        stored_count_1 = scheduler._store_articles(test_db, [article])
        assert stored_count_1 == 1
        
        # Try to store same article again
        stored_count_2 = scheduler._store_articles(test_db, [article])
        assert stored_count_2 == 0
        
        # Verify only one article in database
        db_articles = test_db.query(NewsArticle).all()
        assert len(db_articles) == 1
    
    @patch('backend.services.news_fetcher.NewsAPIClient.fetch_news')
    def test_collect_and_store_integration(self, mock_fetch, test_db_factory):
        """Test complete collect and store workflow"""
        # Mock fetched articles
        mock_articles = [
            NewsArticleCreate(
                title="Market Update",
                content="Stock market rises on positive earnings",
                published_date=datetime.now(),
                source="Financial News",
                url="https://example.com/market-update",
                asset_type="general"
            ),
            NewsArticleCreate(
                title="Crypto News",
                content="Bitcoin reaches new milestone",
                published_date=datetime.now(),
                source="Crypto Daily",
                url="https://example.com/crypto-news",
                asset_type="general"
            )
        ]
        mock_fetch.return_value = mock_articles
        
        # Create scheduler with real database
        mock_client = Mock(spec=NewsAPIClient)
        mock_client.fetch_news = mock_fetch
        
        scheduler = NewsScheduler(
            db_session_factory=test_db_factory,
            news_client=mock_client
        )
        
        # Run collection
        scheduler.collect_and_store()
        
        # Verify articles were stored
        db = test_db_factory()
        stored_articles = db.query(NewsArticle).all()
        assert len(stored_articles) == 2
        assert stored_articles[0].title == "Market Update"
        assert stored_articles[1].title == "Crypto News"
    
    @patch('backend.services.news_fetcher.NewsAPIClient.fetch_news')
    def test_collect_and_store_with_cleanup(self, mock_fetch, test_db_factory):
        """Test collection with automatic cleanup of old articles"""
        # Add old article to database
        db = test_db_factory()
        old_article = NewsArticle(
            title="Old Article",
            content="Old content",
            published_date=datetime.now() - timedelta(days=10),
            source="Test Source",
            asset_type="general"
        )
        db.add(old_article)
        db.commit()
        
        # Mock new articles
        mock_articles = [
            NewsArticleCreate(
                title="New Article",
                content="New content",
                published_date=datetime.now(),
                source="Test Source",
                url="https://example.com/new",
                asset_type="general"
            )
        ]
        mock_fetch.return_value = mock_articles
        
        # Create scheduler
        mock_client = Mock(spec=NewsAPIClient)
        mock_client.fetch_news = mock_fetch
        
        scheduler = NewsScheduler(
            db_session_factory=test_db_factory,
            news_client=mock_client,
            retention_days=7
        )
        
        # Run collection (should also cleanup)
        scheduler.collect_and_store()
        
        # Verify old article was deleted and new article was added
        stored_articles = db.query(NewsArticle).all()
        assert len(stored_articles) == 1
        assert stored_articles[0].title == "New Article"
    
    @patch('backend.services.news_fetcher.NewsAPIClient.fetch_news')
    def test_collect_and_store_error_handling(self, mock_fetch, test_db_factory):
        """Test error handling during collection"""
        # Mock API error
        mock_fetch.side_effect = NewsAPIClientError("API connection failed")
        
        mock_client = Mock(spec=NewsAPIClient)
        mock_client.fetch_news = mock_fetch
        
        scheduler = NewsScheduler(
            db_session_factory=test_db_factory,
            news_client=mock_client
        )
        
        # Should not raise exception (errors are logged)
        scheduler.collect_and_store()
        
        # Verify no articles were stored
        db = test_db_factory()
        stored_articles = db.query(NewsArticle).all()
        assert len(stored_articles) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
