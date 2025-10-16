"""

Test Task 29: Social Sentiment Analysis

"""



import sys

import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))



import pytest

from datetime import datetime, timedelta

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker



from app.database import Base

from models.social_models import (

    SocialPost, SocialSentiment, AggregatedSocialSentiment,

    SocialPostCreate, SocialSentimentCreate

)

from services.social_data_collector import SocialDataCollector

from services.social_sentiment_analyzer import SocialSentimentAnalyzer

from services.integrated_sentiment_service import IntegratedSentimentService

from services.llm_client import LlamaCppClient





# Test database setup

TEST_DATABASE_URL = "sqlite:///./test_social_sentiment.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)





@pytest.fixture(scope="function")

def db():

    """Create test database"""

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:

        yield db

    finally:

        db.close()

        Base.metadata.drop_all(bind=engine)





@pytest.fixture

def mock_llm_client():

    """Mock LLM client for testing"""

    class MockLLMClient:

        def generate(self, prompt, max_tokens=200, temperature=0.3):

            # Return mock sentiment response

            return '''

            {

                "sentiment": "Positive",

                "score": 0.8,

                "confidence": 0.9,

                "reasoning": "Bullish language with rocket emoji"

            }

            '''

    return MockLLMClient()





class TestSocialDataCollector:

    """Test social data collection"""

    

    def test_extract_stock_symbols(self, db):

        """Test stock symbol extraction from text"""

        collector = SocialDataCollector(db)

        

        text = "I'm bullish on $AAPL and $TSLA! ??"

        symbols = collector.extract_stock_symbols(text)

        

        assert len(symbols) == 2

        assert "AAPL" in symbols

        assert "TSLA" in symbols

    

    def test_save_posts(self, db):

        """Test saving posts to database"""

        collector = SocialDataCollector(db)

        

        posts = [

            SocialPostCreate(

                platform="twitter",

                post_id="123456",

                symbol="AAPL",

                author="test_user",

                content="$AAPL to the moon! ??",

                url="https://twitter.com/test",

                likes=100,

                shares=20,

                comments=10,

                created_at=datetime.now()

            )

        ]

        

        saved_count = collector.save_posts(posts)

        assert saved_count == 1

        

        # Verify in database

        post = db.query(SocialPost).filter(SocialPost.post_id == "123456").first()

        assert post is not None

        assert post.symbol == "AAPL"

        assert post.platform == "twitter"

    

    def test_duplicate_posts_not_saved(self, db):

        """Test that duplicate posts are not saved"""

        collector = SocialDataCollector(db)

        

        post_data = SocialPostCreate(

            platform="twitter",

            post_id="123456",

            symbol="AAPL",

            author="test_user",

            content="Test post",

            created_at=datetime.now()

        )

        

        # Save first time

        saved_count1 = collector.save_posts([post_data])

        assert saved_count1 == 1

        

        # Try to save again

        saved_count2 = collector.save_posts([post_data])

        assert saved_count2 == 0

    

    def test_cleanup_old_posts(self, db):

        """Test cleanup of old posts"""

        collector = SocialDataCollector(db)

        

        # Create old post

        old_post = SocialPost(

            platform="twitter",

            post_id="old123",

            content="Old post",

            created_at=datetime.now() - timedelta(days=10)

        )

        db.add(old_post)

        

        # Create recent post

        recent_post = SocialPost(

            platform="twitter",

            post_id="recent123",

            content="Recent post",

            created_at=datetime.now()

        )

        db.add(recent_post)

        db.commit()

        

        # Cleanup posts older than 7 days

        deleted = collector.cleanup_old_posts(days=7)

        assert deleted == 1

        

        # Verify only recent post remains

        remaining = db.query(SocialPost).count()

        assert remaining == 1





class TestSocialSentimentAnalyzer:

    """Test social sentiment analysis"""

    

    def test_create_sentiment_prompt(self, db, mock_llm_client):

        """Test sentiment prompt creation"""

        analyzer = SocialSentimentAnalyzer(db, mock_llm_client)

        

        post = SocialPost(

            id=1,

            platform="twitter",

            post_id="123",

            author="test_user",

            content="$AAPL is going to the moon! 🚀🚀🚀",

            likes=100,

            comments=20,

            created_at=datetime.now()

        )

        

        prompt = analyzer.create_sentiment_prompt(post)

        

        assert "$AAPL is going to the moon!" in prompt

        assert "twitter" in prompt

        assert "100 likes" in prompt

    

    def test_parse_sentiment_response(self, db, mock_llm_client):

        """Test parsing LLM sentiment response"""

        analyzer = SocialSentimentAnalyzer(db, mock_llm_client)

        

        response = '''

        {

            "sentiment": "Positive",

            "score": 0.8,

            "confidence": 0.9,

            "reasoning": "Bullish language"

        }

        '''

        

        result = analyzer.parse_sentiment_response(response)

        

        assert result is not None

        assert result['sentiment'] == "Positive"

        assert result['score'] == 0.8

        assert result['confidence'] == 0.9

    

    def test_analyze_post(self, db, mock_llm_client):

        """Test analyzing a single post"""

        analyzer = SocialSentimentAnalyzer(db, mock_llm_client)

        

        post = SocialPost(

            platform="twitter",

            post_id="123",

            content="$AAPL bullish! ??",

            created_at=datetime.now()

        )

        db.add(post)

        db.commit()

        

        sentiment_data = analyzer.analyze_post(post)

        

        assert sentiment_data is not None

        assert sentiment_data.post_id == post.id

        assert sentiment_data.sentiment in ["Positive", "Negative", "Neutral"]

        assert -1.5 <= sentiment_data.score <= 1.0

        assert 0.0 <= sentiment_data.confidence <= 1.0

    

    def test_get_unanalyzed_posts(self, db, mock_llm_client):

        """Test getting unanalyzed posts"""

        analyzer = SocialSentimentAnalyzer(db, mock_llm_client)

        

        # Create analyzed post

        post1 = SocialPost(

            platform="twitter",

            post_id="123",

            content="Test 1",

            created_at=datetime.now()

        )

        db.add(post1)

        db.commit()

        

        sentiment1 = SocialSentiment(

            post_id=post1.id,

            sentiment="Positive",

            score=0.8,

            confidence=0.9

        )

        db.add(sentiment1)

        

        # Create unanalyzed post

        post2 = SocialPost(

            platform="twitter",

            post_id="456",

            content="Test 2",

            created_at=datetime.now()

        )

        db.add(post2)

        db.commit()

        

        unanalyzed = analyzer.get_unanalyzed_posts()

        

        assert len(unanalyzed) == 1

        assert unanalyzed[0].id == post2.id

    

    def test_aggregate_sentiment(self, db, mock_llm_client):

        """Test sentiment aggregation"""

        analyzer = SocialSentimentAnalyzer(db, mock_llm_client)

        

        # Create posts with sentiment

        for i in range(3):

            post = SocialPost(

                platform="twitter",

                post_id=f"post{i}",

                symbol="AAPL",

                content=f"Test post {i}",

                likes=10 * i,

                shares=5 * i,

                comments=2 * i,

                created_at=datetime.now()

            )

            db.add(post)

            db.commit()

            

            sentiment = SocialSentiment(

                post_id=post.id,

                sentiment="Positive" if i % 2 == 0 else "Negative",

                score=0.5 if i % 2 == 0 else -0.5,

                confidence=0.8

            )

            db.add(sentiment)

        

        db.commit()

        

        aggregated = analyzer.aggregate_sentiment(symbol="AAPL", days=7)

        

        assert "twitter" in aggregated

        assert aggregated["twitter"]["post_count"] == 3

        assert aggregated["twitter"]["positive_count"] == 2

        assert aggregated["twitter"]["negative_count"] == 1

    

    def test_calculate_trending_score(self, db, mock_llm_client):

        """Test trending score calculation"""

        analyzer = SocialSentimentAnalyzer(db, mock_llm_client)

        

        # High engagement, positive sentiment

        score1 = analyzer._calculate_trending_score(0.8, 1000, 10)

        assert score1 > 0

        

        # Low engagement, positive sentiment

        score2 = analyzer._calculate_trending_score(0.8, 10, 10)

        assert score2 < score1

        

        # High engagement, negative sentiment

        score3 = analyzer._calculate_trending_score(-0.8, 1000, 10)

        assert score3 < 0





class TestIntegratedSentimentService:

    """Test integrated sentiment service"""

    

    def test_calculate_combined_score(self, db, mock_llm_client):

        """Test combined score calculation"""

        service = IntegratedSentimentService(db, mock_llm_client)

        

        # News positive, social positive

        social_data = {

            'twitter': {'post_count': 10, 'avg_sentiment': 0.6},

            'reddit': {'post_count': 5, 'avg_sentiment': 0.4}

        }

        

        combined = service._calculate_combined_score(0.8, 20, social_data)

        

        # Should be weighted average: 0.8 * 0.6 + 0.5 * 0.4 = 0.68

        assert 0.4 < combined < 0.8

    

    def test_get_divergence_recommendation(self, db, mock_llm_client):

        """Test divergence recommendation"""

        service = IntegratedSentimentService(db, mock_llm_client)

        

        # Aligned positive

        rec1 = service._get_divergence_recommendation(0.8, 0.7, 0.1)

        assert "buy" in rec1.lower()

        

        # Aligned negative

        rec2 = service._get_divergence_recommendation(-0.8, -0.7, 0.1)

        assert "sell" in rec2.lower()

        

        # Divergent (news positive, social negative)

        rec3 = service._get_divergence_recommendation(0.8, -0.5, 1.3)

        assert "cautious" in rec3.lower()





def test_social_models_creation(db):

    """Test that social models can be created"""

    post = SocialPost(

        platform="twitter",

        post_id="test123",

        symbol="AAPL",

        author="test_user",

        content="Test content",

        likes=10,

        shares=5,

        comments=2,

        created_at=datetime.now()

    )

    db.add(post)

    db.commit()

    

    assert post.id is not None

    

    sentiment = SocialSentiment(

        post_id=post.id,

        sentiment="Positive",

        score=0.8,

        confidence=0.9,

        reasoning="Test reasoning"

    )

    db.add(sentiment)

    db.commit()

    

    assert sentiment.id is not None





def test_aggregated_sentiment_creation(db):

    """Test aggregated sentiment model"""

    agg = AggregatedSocialSentiment(

        symbol="AAPL",

        date=datetime.now(),

        platform="twitter",

        post_count=100,

        avg_sentiment_score=0.5,

        positive_count=60,

        negative_count=20,

        neutral_count=20,

        total_engagement=5000

    )

    db.add(agg)

    db.commit()

    

    assert agg.id is not None





if __name__ == "__main__":

    print("Running Task 29 Social Sentiment Tests...")

    pytest.main([__file__, "-v", "--tb=short"])

