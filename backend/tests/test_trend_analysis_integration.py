"""

Integration tests for trend analysis modules



Tests the complete pipeline:

1. TrendAggregator

2. RecommendationEngine

3. CacheService



Note: These tests require:

- Database with sentiment analysis data

- llama.cpp server running (or use mocks)

"""



import pytest

from datetime import datetime, timedelta

from unittest.mock import Mock, patch, MagicMock

import sys

import os



# Add parent directory to path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



from services.trend_aggregator import TrendAggregator, TrendSummary

from services.recommendation_engine import RecommendationEngine, Recommendation

from services.cache_service import CacheService, make_analysis_cache_key

from models import SentimentAnalysis, NewsArticle





class TestTrendAggregatorIntegration:

    """Integration tests for TrendAggregator"""

    

    def test_aggregate_weekly_trend_with_mock_data(self, db_session, sample_sentiments):

        """Test trend aggregation with mock sentiment data"""

        # Create mock LLM client

        mock_llm = Mock()

        mock_llm.generate_json.return_value = {

            "summary_text": "?�장?� ?�반?�으�?긍정?�인 ?�름??보이�??�습?�다.",

            "dominant_sentiment": "Positive",

            "key_drivers": ["경제 ?�장", "기업 ?�적 개선", "_책 지"
        assert trend.summary_text != ""

        assert trend.dominant_sentiment in ["Positive", "Negative", "Neutral"]

        assert len(trend.key_drivers) > 0

        assert trend.total_articles > 0

        

        # Verify LLM was called

        mock_llm.generate_json.assert_called_once()

        

        aggregator.close()

    

    def test_aggregate_with_no_data(self, db_session):

        """Test aggregation with no sentiment data"""

        mock_llm = Mock()

        aggregator = TrendAggregator(llama_client=mock_llm)

        

        # Should raise ValueError

        with pytest.raises(ValueError, match="No sentiment data found"):

            aggregator.aggregate_weekly_trend(db_session, days=7)

        

        aggregator.close()

    

    def test_calculate_statistics(self, sample_sentiments):

        """Test statistics calculation"""

        aggregator = TrendAggregator()

        

        stats = aggregator._calculate_statistics(sample_sentiments)

        

        assert stats["total_count"] == len(sample_sentiments)

        assert stats["positive_count"] >= 0

        assert stats["negative_count"] >= 0

        assert stats["neutral_count"] >= 0

        assert "average_score" in stats

        assert "daily_scores" in stats

        

        aggregator.close()





class TestRecommendationEngineIntegration:

    """Integration tests for RecommendationEngine"""

    

    def test_generate_recommendation_with_mock(self, sample_trend_summary):

        """Test recommendation generation with mock LLM"""

        # Create mock LLM client

        mock_llm = Mock()

        mock_llm.generate_json.return_value = {

            "recommendation": "?�재 ?�장 ?�황??고려?????�중??매수�?권장?�니??",

            "confidence": "medium",

            "risk_assessment": "중간 _�"
            "key_considerations": ["변?�성 모니?�링", "분산 ?�자", "?�절�??�정"]

        }

        

        # Create mock VIX fetcher

        mock_vix = Mock()

        mock_vix.get_current_vix.return_value = 18.5

        mock_vix.normalize_vix.return_value = 0.28

        

        # Create engine with mocks

        engine = RecommendationEngine(

            llama_client=mock_llm,

            vix_fetcher=mock_vix

        )

        

        # Generate recommendation

        recommendation = engine.generate_recommendation(

            trend=sample_trend_summary,

            vix=18.5

        )

        

        # Verify result

        assert isinstance(recommendation, Recommendation)

        assert 0 <= recommendation.buy_sell_ratio <= 100

        assert recommendation.confidence in ["low", "medium", "high"]

        assert recommendation.recommendation != ""

        assert recommendation.risk_assessment != ""

        assert len(recommendation.key_considerations) > 0

        

        # Verify LLM was called

        mock_llm.generate_json.assert_called_once()

        

        engine.close()

    

    def test_assess_volatility(self):

        """Test volatility assessment"""

        engine = RecommendationEngine()

        

        assert "??��" in engine._assess_volatility(12.0)

        assert "보통" in engine._assess_volatility(18.0)

        assert "?�음" in engine._assess_volatility(25.0)

        assert "매우 ?�음" in engine._assess_volatility(35.0)

        

        engine.close()





class TestCacheServiceIntegration:

    """Integration tests for CacheService"""

    

    def test_cache_set_and_get(self, db_session):

        """Test basic cache operations"""

        cache = CacheService(expiry_hours=1)

        

        # Set cache

        cache_key = "test_key_123"

        result = {"ratio": 65, "summary": "Test summary"}

        

        cache.set(db_session, cache_key, result)

        

        # Get cache

        cached = cache.get(db_session, cache_key)

        

        assert cached is not None

        assert cached["ratio"] == 65

        assert cached["summary"] == "Test summary"

    

    def test_cache_expiration(self, db_session):

        """Test cache expiration logic"""

        cache = CacheService(expiry_hours=0)  # Expire immediately

        

        cache_key = "test_expire"

        result = {"data": "test"}

        

        # Set cache with 0 hour expiry

        cache.set(db_session, cache_key, result, expiry_hours=0)

        

        # Should be expired immediately

        cached = cache.get(db_session, cache_key)

        assert cached is None

    

    def test_cache_update(self, db_session):

        """Test updating existing cache entry"""

        cache = CacheService()

        

        cache_key = "test_update"

        

        # Set initial value

        cache.set(db_session, cache_key, {"value": 1})

        

        # Update value

        cache.set(db_session, cache_key, {"value": 2})

        

        # Get updated value

        cached = cache.get(db_session, cache_key)

        assert cached["value"] == 2

    

    def test_cleanup_expired(self, db_session):

        """Test cleanup of expired entries"""

        cache = CacheService()

        

        # Create expired entry

        cache.set(db_session, "expired_1", {"data": 1}, expiry_hours=0)

        cache.set(db_session, "expired_2", {"data": 2}, expiry_hours=0)

        

        # Create active entry

        cache.set(db_session, "active", {"data": 3}, expiry_hours=1)

        

        # Cleanup

        deleted = cache.cleanup_expired(db_session)

        

        assert deleted >= 2

        

        # Active entry should still exist

        assert cache.get(db_session, "active") is not None

    

    def test_cache_stats(self, db_session):

        """Test cache statistics"""

        cache = CacheService()

        

        # Add some entries

        cache.set(db_session, "stat_1", {"data": 1})

        cache.set(db_session, "stat_2", {"data": 2})

        

        stats = cache.get_cache_stats(db_session)

        

        assert stats["total_entries"] >= 2

        assert stats["active_entries"] >= 0

        assert stats["expired_entries"] >= 0





class TestCompletePipeline:

    """Integration test for complete analysis pipeline"""

    

    def test_full_pipeline_with_mocks(self, db_session, sample_sentiments, sample_news_articles):

        """Test complete pipeline from sentiment data to cached recommendation"""

        # Setup mocks

        mock_llm = Mock()

        

        # Mock trend aggregation response

        mock_llm.generate_json.side_effect = [

            # First call: trend aggregation

            {

                "summary_text": "?�장?� 긍정???�름??보이�??�습?�다.",

                "dominant_sentiment": "Positive",

                "key_drivers": ["경제 ?�장", "?�적 개선"]

            },

            # Second call: recommendation

            {

                "recommendation": "?�중??매수�?권장?�니??",

                "confidence": "medium",

                "risk_assessment": "중간 리스??,

                "key_considerations": ["변?�성 주의", "분산 ?�자"]

            }

        ]

        

        mock_vix = Mock()

        mock_vix.get_current_vix.return_value = 18.5

        mock_vix.normalize_vix.return_value = 0.28

        

        # Initialize services

        cache = CacheService()

        aggregator = TrendAggregator(llama_client=mock_llm)

        engine = RecommendationEngine(

            llama_client=mock_llm,

            vix_fetcher=mock_vix

        )

        

        # Check cache (should be empty)

        cache_key = make_analysis_cache_key("general", 7)

        cached = cache.get(db_session, cache_key)

        assert cached is None

        

        # Run pipeline

        # Step 1: Aggregate trend

        trend = aggregator.aggregate_weekly_trend(db_session, days=7)

        assert isinstance(trend, TrendSummary)

        

        # Step 2: Generate recommendation

        recommendation = engine.generate_recommendation(trend)

        assert isinstance(recommendation, Recommendation)

        

        # Step 3: Cache result

        result = {

            "buy_sell_ratio": recommendation.buy_sell_ratio,

            "recommendation": recommendation.recommendation,

            "trend_summary": trend.summary_text

        }

        cache.set(db_session, cache_key, result)

        

        # Verify cache

        cached = cache.get(db_session, cache_key)

        assert cached is not None

        assert cached["buy_sell_ratio"] == recommendation.buy_sell_ratio

        

        # Cleanup

        aggregator.close()

        engine.close()





# Fixtures



@pytest.fixture

def sample_sentiments():

    """Create sample sentiment analysis objects"""

    sentiments = []

    base_date = datetime.now() - timedelta(days=6)

    

    for i in range(7):

        date = base_date + timedelta(days=i)

        

        # Mix of positive, negative, neutral

        if i % 3 == 0:

            sentiment = "Positive"

            score = 1.0

        elif i % 3 == 1:

            sentiment = "Negative"

            score = -1.5

        else:

            sentiment = "Neutral"

            score = 0.0

        

        s = SentimentAnalysis(

            id=i + 1,

            article_id=i + 1,

            sentiment=sentiment,

            score=score,

            reasoning=f"Test reasoning {i}",

            analyzed_at=date

        )

        sentiments.append(s)

    

    return sentiments





@pytest.fixture

def sample_news_articles():

    """Create sample news article objects"""

    articles = []

    base_date = datetime.now() - timedelta(days=6)

    

    for i in range(7):

        date = base_date + timedelta(days=i)

        

        article = NewsArticle(

            id=i + 1,

            title=f"Test Article {i}",

            content=f"Test content for article {i}",

            published_date=date,

            source="Test Source",

            url=f"http://test.com/article{i}"

        )

        articles.append(article)

    

    return articles





@pytest.fixture

def sample_trend_summary():

    """Create sample TrendSummary object"""

    return TrendSummary(

        summary_text="?�장?� ?�반?�으�?긍정?�인 ?�름??보이�??�습?�다.",

        dominant_sentiment="Positive",

        key_drivers=["경제 ?�장", "기업 ?�적 개선"],

        period_start=datetime.now() - timedelta(days=7),

        period_end=datetime.now(),

        total_articles=50,

        average_score=0.5

    )





@pytest.fixture

def db_session():

    """Create mock database session"""

    session = MagicMock()

    

    # Mock query methods

    query_mock = MagicMock()

    session.query.return_value = query_mock

    query_mock.filter.return_value = query_mock

    query_mock.order_by.return_value = query_mock

    query_mock.limit.return_value = query_mock

    query_mock.first.return_value = None

    query_mock.all.return_value = []

    query_mock.count.return_value = 0

    

    return session





if __name__ == "__main__":

    pytest.main([__file__, "-v"])

