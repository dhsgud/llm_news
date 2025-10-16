"""
API Endpoint Integration Tests

Tests all API endpoints with various scenarios including:
- Successful requests
- Error cases
- Edge cases
- Validation errors

Requirements: 6.2, 6.3
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path to allow backend imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import the FastAPI app
try:
    from main import app
except ModuleNotFoundError:
    # Fallback for different execution contexts
    import main
    app = main.app


# Create test client fixture
@pytest.fixture(scope="module")
def client():
    """Create test client"""
    test_client = TestClient(app)
    yield test_client


class TestRootEndpoints:
    """Test root and health check endpoints"""
    
    def test_root_endpoint(self, client):
        """Test GET / returns app info"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
    
    def test_health_check_endpoint(self, client):
        """Test GET /health returns health status"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "llama_cpp" in data


class TestAnalyzeEndpoint:
    """Test POST /api/analyze endpoint"""
    
    def test_analyze_success_with_cache(self, client):
        """Test successful analysis with cached result"""
        from models import SentimentResult
        from services.recommendation_engine import Recommendation
        
        cached_result = {
            "buy_sell_ratio": 65,
            "trend_summary": "?�장?� 긍정?�입?�다.",
            "recommendation": "?�중??매수�?권장?�니??",
            "confidence": "medium",
            "risk_assessment": "중간 리스??,
            "key_considerations": ["변?�성 주의"],
            "vix": 18.5,
            "signal_score": 0.5,
            "last_updated": datetime.now().isoformat()
        }
        
        with patch('api.market.CacheService') as mock_cache:
            mock_cache_instance = Mock()
            mock_cache.return_value = mock_cache_instance
            mock_cache_instance.get_cached_result.return_value = cached_result
            
            response = client.post("/api/analyze?asset_type=general")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["buy_sell_ratio"] == 65
            assert data["trend_summary"] == "?�장?� 긍정?�입?�다."
            assert data["confidence"] == "medium"
    
    def test_analyze_insufficient_data_error(self, client):
        """Test analysis with insufficient data"""
        with patch('api.market.CacheService') as mock_cache, \
             patch('api.market.TrendAggregator') as mock_aggregator:
            
            mock_cache_instance = Mock()
            mock_cache.return_value = mock_cache_instance
            mock_cache_instance.get_cached_result.return_value = None
            
            mock_agg_instance = Mock()
            mock_aggregator.return_value = mock_agg_instance
            mock_agg_instance.aggregate_weekly_trend.side_effect = ValueError(
                "No sentiment data found"
            )
            
            response = client.post("/api/analyze")
            
            assert response.status_code == 400
            data = response.json()
            assert "detail" in data


class TestNewsEndpoint:
    """Test GET /api/news endpoint"""
    
    def test_get_news_success(self, client):
        """Test successful news retrieval"""
        from models import NewsArticle, SentimentAnalysis
        
        mock_articles = []
        for i in range(5):
            article = Mock(spec=NewsArticle)
            article.id = i + 1
            article.title = f"Test Article {i}"
            article.content = f"Content {i}"
            article.published_date = datetime.now() - timedelta(days=i)
            article.source = "Test Source"
            article.url = f"http://test.com/{i}"
            mock_articles.append(article)
        
        with patch('api.market.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            query_mock = MagicMock()
            mock_db.query.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = mock_articles
            query_mock.first.return_value = None
            
            response = client.get("/api/news?days=7&limit=50")
            
            assert response.status_code == 200
            data = response.json()
            
            assert isinstance(data, list)
            assert len(data) == 5
    
    def test_get_news_invalid_parameters(self, client):
        """Test news endpoint with invalid parameters"""
        response = client.get("/api/news?days=100")
        assert response.status_code == 422
        
        response = client.get("/api/news?limit=500")
        assert response.status_code == 422
    
    def test_get_news_empty_result(self, client):
        """Test news retrieval with no articles"""
        with patch('api.market.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            query_mock = MagicMock()
            mock_db.query.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.limit.return_value = query_mock
            query_mock.all.return_value = []
            
            response = client.get("/api/news")
            
            assert response.status_code == 200
            data = response.json()
            assert data == []


class TestDailySentimentEndpoint:
    """Test GET /api/sentiment/daily endpoint"""
    
    def test_get_daily_sentiment_success(self, client):
        """Test successful daily sentiment retrieval"""
        from models import SentimentAnalysis
        
        mock_sentiments = []
        base_date = datetime.now() - timedelta(days=6)
        
        for i in range(7):
            for j in range(3):
                sentiment = Mock(spec=SentimentAnalysis)
                sentiment.analyzed_at = base_date + timedelta(days=i)
                sentiment.score = 0.5 if j % 2 == 0 else -0.5
                sentiment.sentiment = "Positive" if j % 2 == 0 else "Negative"
                mock_sentiments.append(sentiment)
        
        with patch('api.market.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            query_mock = MagicMock()
            mock_db.query.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.all.return_value = mock_sentiments
            
            response = client.get("/api/sentiment/daily?days=7")
            
            assert response.status_code == 200
            data = response.json()
            
            assert isinstance(data, list)
            assert len(data) == 7
            
            first_day = data[0]
            assert "date" in first_day
            assert "average_score" in first_day
            assert "article_count" in first_day
            assert "positive_count" in first_day
            assert "negative_count" in first_day
            assert "neutral_count" in first_day
    
    def test_get_daily_sentiment_no_data(self, client):
        """Test daily sentiment with no data"""
        with patch('api.market.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            query_mock = MagicMock()
            mock_db.query.return_value = query_mock
            query_mock.filter.return_value = query_mock
            query_mock.order_by.return_value = query_mock
            query_mock.all.return_value = []
            
            response = client.get("/api/sentiment/daily")
            
            assert response.status_code == 200
            data = response.json()
            assert data == []
    
    def test_get_daily_sentiment_invalid_parameters(self, client):
        """Test daily sentiment with invalid parameters"""
        response = client.get("/api/sentiment/daily?days=100")
        assert response.status_code == 422
        
        response = client.get("/api/sentiment/daily?days=0")
        assert response.status_code == 422


class TestResponseHeaders:
    """Test response headers and middleware"""
    
    def test_process_time_header(self, client):
        """Test that X-Process-Time header is added"""
        response = client.get("/")
        
        assert "x-process-time" in response.headers
        process_time = float(response.headers["x-process-time"])
        assert process_time >= 0


class TestErrorHandling:
    """Test error handling and exception responses"""
    
    def test_404_not_found(self, client):
        """Test 404 for non-existent endpoint"""
        response = client.get("/api/nonexistent")
        
        assert response.status_code == 404
    
    def test_405_method_not_allowed(self, client):
        """Test 405 for wrong HTTP method"""
        response = client.get("/api/analyze")
        
        assert response.status_code == 405
    
    def test_validation_error_response_format(self, client):
        """Test validation error response format"""
        response = client.get("/api/news?days=invalid")
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
