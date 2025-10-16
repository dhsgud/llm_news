"""

Test Task 15: Stock API Endpoints



Tests the three new stock-related API endpoints:

1. GET /api/stocks/{symbol} - Stock information and price history

2. GET /api/stocks/{symbol}/sentiment - Stock-specific sentiment analysis

3. GET /api/account/holdings - Account holdings summary

"""



import pytest

from datetime import datetime, timedelta

from decimal import Decimal

from fastapi.testclient import TestClient

from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker



from main import app

from app.database import Base, get_db

from models import (

    StockPrice, AccountHolding, NewsArticle, 

    SentimentAnalysis, StockNewsRelation

)





# Test database setup - use in-memory database

TEST_DATABASE_URL = "sqlite:///:memory:"





@pytest.fixture(scope="function")

def setup_database():

    """Create test database and tables for each test"""

    # Create a new engine for each test

    test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    

    # Create tables

    Base.metadata.create_all(bind=test_engine)

    

    # Override get_db dependency

    def override_get_db():

        try:

            db = TestingSessionLocal()

            yield db

        finally:

            db.close()

    

    app.dependency_overrides[get_db] = override_get_db

    

    yield TestingSessionLocal

    

    # Clean up

    Base.metadata.drop_all(bind=test_engine)

    app.dependency_overrides.clear()





client = TestClient(app)





@pytest.fixture

def sample_stock_data(setup_database):

    """Create sample stock price data"""

    SessionLocal = setup_database

    db = SessionLocal()

    

    # Create stock prices for Samsung (005930)

    now = datetime.now()

    prices = []

    for i in range(24):  # 24 hours of data

        price = StockPrice(

            symbol="005930",

            price=Decimal("70000") + Decimal(i * 100),

            volume=1000000 + i * 10000,

            open_price=Decimal("69500"),

            high_price=Decimal("71000"),

            low_price=Decimal("69000"),

            timestamp=now - timedelta(hours=23-i)

        )

        prices.append(price)

        db.add(price)

    

    # Create stock prices for SK Hynix (000660)

    for i in range(12):

        price = StockPrice(

            symbol="000660",

            price=Decimal("120000") + Decimal(i * 200),

            volume=500000 + i * 5000,

            open_price=Decimal("119000"),

            high_price=Decimal("122000"),

            low_price=Decimal("118000"),

            timestamp=now - timedelta(hours=11-i)

        )

        db.add(price)

    

    db.commit()

    db.close()

    

    return {"samsung_prices": 24, "sk_hynix_prices": 12}





@pytest.fixture

def sample_sentiment_data(setup_database):

    """Create sample news and sentiment data"""

    SessionLocal = setup_database

    db = SessionLocal()

    

    # Create news articles

    now = datetime.now()

    articles = []

    

    for i in range(5):

        article = NewsArticle(

            title=f"삼성전자 관련 뉴스 {i+1}",

            content=f"삼성전자의 최신 소식입니다. 내용 {i+1}",

            published_date=now - timedelta(days=i),

            source="_스"
            url=f"https://test.com/news/{i+1}",

            asset_type="stock"

        )

        db.add(article)

        db.flush()

        articles.append(article)

        

        # Create sentiment analysis

        sentiment_score = 0.5 if i % 2 == 0 else -0.3

        sentiment_type = "Positive" if sentiment_score > 0 else "Negative"

        

        sentiment = SentimentAnalysis(

            article_id=article.id,

            sentiment=sentiment_type,

            score=sentiment_score,

            reasoning=f"뉴스 분석 {i+1}",

            analyzed_at=now - timedelta(days=i)

        )

        db.add(sentiment)

        

        # Create stock-news relation

        relation = StockNewsRelation(

            stock_symbol="005930",

            article_id=article.id,

            relevance_score=0.8

        )

        db.add(relation)

    

    db.commit()

    db.close()

    

    return {"article_count": 5}





@pytest.fixture

def sample_holdings_data(setup_database):

    """Create sample account holdings"""

    SessionLocal = setup_database

    db = SessionLocal()

    

    # Create holdings

    holdings = [

        AccountHolding(

            symbol="005930",

            quantity=100,

            average_price=Decimal("65000"),

            current_price=Decimal("70000"),

            updated_at=datetime.now()

        ),

        AccountHolding(

            symbol="000660",

            quantity=50,

            average_price=Decimal("115000"),

            current_price=Decimal("120000"),

            updated_at=datetime.now()

        ),

        AccountHolding(

            symbol="035420",

            quantity=20,

            average_price=Decimal("200000"),

            current_price=Decimal("195000"),

            updated_at=datetime.now()

        )

    ]

    

    for holding in holdings:

        db.add(holding)

    

    db.commit()

    db.close()

    

    return {"holding_count": 3}





class TestStockInfoEndpoint:

    """Test GET /api/stocks/{symbol} endpoint"""

    

    def test_get_stock_info_success(self, sample_stock_data):

        """Test successful stock info retrieval"""

        response = client.get("/api/stocks/005930?hours=24")

        

        assert response.status_code == 200

        data = response.json()

        

        assert data["symbol"] == "005930"

        assert data["current_price"] is not None

        assert data["volume"] is not None

        assert data["open_price"] is not None

        assert data["high_price"] is not None

        assert data["low_price"] is not None

        assert data["last_updated"] is not None

        assert len(data["price_history"]) == 24

    

    def test_get_stock_info_limited_history(self, sample_stock_data):

        """Test stock info with limited history"""

        response = client.get("/api/stocks/005930?hours=12")

        

        assert response.status_code == 200

        data = response.json()

        

        # Should have approximately 12 hours of data

        assert len(data["price_history"]) <= 13  # Allow for timing variations

    

    def test_get_stock_info_not_found(self, setup_database):

        """Test stock info for non-existent symbol"""

        response = client.get("/api/stocks/999999?hours=24")

        

        assert response.status_code == 404

        assert "No price data found" in response.json()["detail"]

    

    def test_get_stock_info_invalid_hours(self, sample_stock_data):

        """Test with invalid hours parameter"""

        # Hours too low

        response = client.get("/api/stocks/005930?hours=0")

        assert response.status_code == 422

        

        # Hours too high

        response = client.get("/api/stocks/005930?hours=200")

        assert response.status_code == 422

    

    def test_price_history_ordering(self, sample_stock_data):

        """Test that price history is ordered chronologically"""

        response = client.get("/api/stocks/005930?hours=24")

        

        assert response.status_code == 200

        data = response.json()

        

        timestamps = [item["timestamp"] for item in data["price_history"]]

        # Verify ascending order

        assert timestamps == sorted(timestamps)





class TestStockSentimentEndpoint:

    """Test GET /api/stocks/{symbol}/sentiment endpoint"""

    

    def test_get_stock_sentiment_success(self, sample_sentiment_data):

        """Test successful sentiment analysis retrieval"""

        response = client.get("/api/stocks/005930/sentiment?days=7")

        

        assert response.status_code == 200

        data = response.json()

        

        assert data["symbol"] == "005930"

        assert "average_score" in data

        assert "sentiment_distribution" in data

        assert data["article_count"] == 5

        assert "related_news" in data

        assert data["recommendation"] in ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]

        assert data["confidence"] in ["Low", "Medium", "High"]

    

    def test_sentiment_recommendation_logic(self, sample_sentiment_data):

        """Test sentiment-based recommendation logic"""

        response = client.get("/api/stocks/005930/sentiment?days=7")

        

        assert response.status_code == 200

        data = response.json()

        

        avg_score = data["average_score"]

        recommendation = data["recommendation"]

        

        # Verify recommendation matches score

        if avg_score > 0.5:

            assert recommendation == "Strong Buy"

        elif avg_score > 0.2:

            assert recommendation == "Buy"

        elif avg_score > -0.2:

            assert recommendation == "Hold"

        elif avg_score > -0.5:

            assert recommendation == "Sell"

        else:

            assert recommendation == "Strong Sell"

    

    def test_get_stock_sentiment_not_found(self, setup_database):

        """Test sentiment for stock with no data"""

        response = client.get("/api/stocks/999999/sentiment?days=7")

        

        assert response.status_code == 404

        assert "No sentiment data available" in response.json()["detail"]

    

    def test_get_stock_sentiment_invalid_days(self, sample_sentiment_data):

        """Test with invalid days parameter"""

        # Days too low

        response = client.get("/api/stocks/005930/sentiment?days=0")

        assert response.status_code == 422

        

        # Days too high

        response = client.get("/api/stocks/005930/sentiment?days=31")

        assert response.status_code == 422

    

    def test_related_news_limit(self, sample_sentiment_data):

        """Test that related news is limited to 10 items"""

        response = client.get("/api/stocks/005930/sentiment?days=7")

        

        assert response.status_code == 200

        data = response.json()

        

        # Should have at most 10 news items

        assert len(data["related_news"]) <= 10

    

    def test_sentiment_distribution(self, sample_sentiment_data):

        """Test sentiment distribution calculation"""

        response = client.get("/api/stocks/005930/sentiment?days=7")

        

        assert response.status_code == 200

        data = response.json()

        

        distribution = data["sentiment_distribution"]

        

        # Should have counts for each sentiment type

        assert "Positive" in distribution or "Negative" in distribution or "Neutral" in distribution

        

        # Total should match article count

        total = sum(distribution.values())

        assert total == data["article_count"]





class TestAccountHoldingsEndpoint:

    """Test GET /api/account/holdings endpoint"""

    

    def test_get_holdings_success(self, sample_holdings_data):

        """Test successful holdings retrieval"""

        response = client.get("/api/account/holdings")

        

        assert response.status_code == 200

        data = response.json()

        

        assert data["total_holdings"] == 3

        assert "total_value" in data

        assert "total_cost" in data

        assert "profit_loss" in data

        assert "profit_loss_percentage" in data

        assert len(data["holdings"]) == 3

        assert "last_updated" in data

    

    def test_holdings_profit_loss_calculation(self, sample_holdings_data):

        """Test profit/loss calculation accuracy"""

        response = client.get("/api/account/holdings")

        

        assert response.status_code == 200

        data = response.json()

        

        # Calculate expected values

        # Samsung: 100 * 65000 = 6,500,000 cost, 100 * 70000 = 7,000,000 value

        # SK Hynix: 50 * 115000 = 5,750,000 cost, 50 * 120000 = 6,000,000 value

        # NAVER: 20 * 200000 = 4,000,000 cost, 20 * 195000 = 3,900,000 value

        

        expected_cost = Decimal("6500000") + Decimal("5750000") + Decimal("4000000")

        expected_value = Decimal("7000000") + Decimal("6000000") + Decimal("3900000")

        expected_pl = expected_value - expected_cost

        expected_pl_pct = float((expected_pl / expected_cost * 100))

        

        assert abs(float(data["total_cost"]) - float(expected_cost)) < 0.01

        assert abs(float(data["total_value"]) - float(expected_value)) < 0.01

        assert abs(float(data["profit_loss"]) - float(expected_pl)) < 0.01

        assert abs(data["profit_loss_percentage"] - expected_pl_pct) < 0.01

    

    def test_get_holdings_empty(self, setup_database):

        """Test holdings endpoint with no holdings"""

        response = client.get("/api/account/holdings")

        

        assert response.status_code == 200

        data = response.json()

        

        assert data["total_holdings"] == 0

        assert float(data["total_value"]) == 0.0

        assert float(data["total_cost"]) == 0.0

        assert float(data["profit_loss"]) == 0.0

        assert data["profit_loss_percentage"] == 0.0

        assert len(data["holdings"]) == 0

    

    def test_holdings_response_structure(self, sample_holdings_data):

        """Test holdings response structure"""

        response = client.get("/api/account/holdings")

        

        assert response.status_code == 200

        data = response.json()

        

        # Check each holding has required fields

        for holding in data["holdings"]:

            assert "id" in holding

            assert "symbol" in holding

            assert "quantity" in holding

            assert "average_price" in holding

            assert "current_price" in holding

            assert "updated_at" in holding





class TestAccountSyncEndpoint:

    """Test POST /api/account/sync endpoint"""

    

    def test_sync_not_implemented(self, setup_database):

        """Test that sync endpoint returns not implemented"""

        response = client.post("/api/account/sync")

        

        assert response.status_code == 501

        assert "brokerage API configuration" in response.json()["detail"]





class TestIntegration:

    """Integration tests for stock endpoints"""

    

    def test_stock_info_and_sentiment_integration(self, sample_stock_data, sample_sentiment_data):

        """Test that stock info and sentiment work together"""

        # Get stock info

        info_response = client.get("/api/stocks/005930?hours=24")

        assert info_response.status_code == 200

        

        # Get sentiment

        sentiment_response = client.get("/api/stocks/005930/sentiment?days=7")

        assert sentiment_response.status_code == 200

        

        # Both should return data for the same symbol

        assert info_response.json()["symbol"] == sentiment_response.json()["symbol"]

    

    def test_holdings_with_price_data(self, sample_holdings_data, sample_stock_data):

        """Test holdings endpoint with corresponding price data"""

        holdings_response = client.get("/api/account/holdings")

        assert holdings_response.status_code == 200

        

        holdings_data = holdings_response.json()

        

        # Check that we can get price info for held stocks

        for holding in holdings_data["holdings"]:

            symbol = holding["symbol"]

            price_response = client.get(f"/api/stocks/{symbol}?hours=24")

            

            # Should succeed for Samsung (005930) and SK Hynix (000660)

            if symbol in ["005930", "000660"]:

                assert price_response.status_code == 200





def test_api_documentation():

    """Test that API documentation is accessible"""

    response = client.get("/docs")

    assert response.status_code == 200





def test_openapi_schema():

    """Test that OpenAPI schema includes new endpoints"""

    response = client.get("/openapi.json")

    assert response.status_code == 200

    

    schema = response.json()

    paths = schema["paths"]

    

    # Verify new endpoints are in schema

    assert "/api/stocks/{symbol}" in paths

    assert "/api/stocks/{symbol}/sentiment" in paths

    assert "/api/account/holdings" in paths

    assert "/api/account/sync" in paths





if __name__ == "__main__":

    pytest.main([__file__, "-v", "--tb=short"])

