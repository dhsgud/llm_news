"""

Tests for SentimentAnalyzer module

"""



import pytest

import sys

import os

from datetime import datetime

from unittest.mock import Mock, MagicMock, patch



# Add parent directory to path for imports

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))



from services.sentiment_analyzer import (

    SentimentAnalyzer,

    SentimentQuantifier,

    STEP1_SYSTEM_PROMPT,

    STEP1_USER_PROMPT_TEMPLATE

)

from models import NewsArticle, SentimentResult





class TestSentimentQuantifier:

    """Test sentiment score quantification"""

    

    def test_quantify_positive(self):

        """Test positive sentiment quantification"""

        score = SentimentQuantifier.quantify("Positive")

        assert score == 1.0

    

    def test_quantify_negative(self):

        """Test negative sentiment quantification with conservative weight"""

        score = SentimentQuantifier.quantify("Negative")

        assert score == -1.5  # -1.0 * 1.5 weight

    

    def test_quantify_neutral(self):

        """Test neutral sentiment quantification"""

        score = SentimentQuantifier.quantify("Neutral")

        assert score == 0.0

    

    def test_calculate_daily_score(self):

        """Test daily score calculation"""

        sentiments = [

            SentimentResult(

                article_id=1,

                sentiment="Positive",

                score=1.0,

                reasoning="Good news",

                analyzed_at=datetime.now()

            ),

            SentimentResult(

                article_id=2,

                sentiment="Negative",

                score=-1.5,

                reasoning="Bad news",

                analyzed_at=datetime.now()

            ),

            SentimentResult(

                article_id=3,

                sentiment="Neutral",

                score=0.0,

                reasoning="Neutral news",

                analyzed_at=datetime.now()

            )

        ]

        

        daily_score = SentimentQuantifier.calculate_daily_score(sentiments)

        expected = (1.0 + (-1.5) + 0.0) / 3

        assert daily_score == pytest.approx(expected)

    

    def test_calculate_daily_score_empty(self):

        """Test daily score with empty list"""

        score = SentimentQuantifier.calculate_daily_score([])

        assert score == 0.0





class TestPromptGeneration:

    """Test prompt generation for sentiment analysis"""

    

    @pytest.fixture

    def sample_article(self):

        """Create sample NewsArticle"""

        article = Mock(spec=NewsArticle)

        article.id = 1

        article.title = "Stock Market Rises on Positive Economic Data"

        article.content = "The stock market showed strong gains today with major indices up 2%"

        article.source = "Financial Times"

        article.published_date = datetime(2025, 10, 7, 10, 30)

        return article

    

    def test_system_prompt_structure(self):

        """Test that system prompt has required structure"""

        assert "금융 분석가" in STEP1_SYSTEM_PROMPT

        assert "감성" in STEP1_SYSTEM_PROMPT

        assert "Positive" in STEP1_SYSTEM_PROMPT

        assert "Negative" in STEP1_SYSTEM_PROMPT

        assert "Neutral" in STEP1_SYSTEM_PROMPT

        assert "JSON" in STEP1_SYSTEM_PROMPT

    

    def test_user_prompt_template_placeholders(self):

        """Test that user prompt template has all required placeholders"""

        assert "{title}" in STEP1_USER_PROMPT_TEMPLATE

        assert "{content}" in STEP1_USER_PROMPT_TEMPLATE

        assert "{source}" in STEP1_USER_PROMPT_TEMPLATE

        assert "{published_date}" in STEP1_USER_PROMPT_TEMPLATE

    

    def test_user_prompt_formatting(self, sample_article):

        """Test user prompt formatting with article data"""

        user_prompt = STEP1_USER_PROMPT_TEMPLATE.format(

            title=sample_article.title,

            content=sample_article.content,

            source=sample_article.source,

            published_date=sample_article.published_date.strftime("%Y-%m-%d %H:%M")

        )

        

        assert sample_article.title in user_prompt

        assert sample_article.content in user_prompt

        assert sample_article.source in user_prompt

        assert "2025-10-07 10:30" in user_prompt

        assert "다음 뉴스 기사를 분석해주세요" in user_prompt

    

    def test_prompt_content_truncation(self):

        """Test that long content is properly handled"""

        long_content = "A" * 5000  # Very long content

        article = Mock(spec=NewsArticle)

        article.id = 1

        article.title = "Test"

        article.content = long_content

        article.source = "Test"

        article.published_date = datetime.now()

        

        # Simulate truncation (as done in analyze_article)

        truncated_content = article.content[:2000]

        

        user_prompt = STEP1_USER_PROMPT_TEMPLATE.format(

            title=article.title,

            content=truncated_content,

            source=article.source,

            published_date=article.published_date.strftime("%Y-%m-%d %H:%M")

        )

        

        # Verify content is truncated

        assert len(truncated_content) == 2000

        assert truncated_content in user_prompt





class TestScoreCalculation:

    """Test score calculation and quantification"""

    

    def test_positive_score_value(self):

        """Test positive sentiment score is exactly 1.0"""

        score = SentimentQuantifier.quantify("Positive")

        assert score == 1.0

        assert isinstance(score, float)

    

    def test_negative_score_value(self):

        """Test negative sentiment score with conservative weight"""

        score = SentimentQuantifier.quantify("Negative")

        assert score == -1.5

        assert score == SentimentQuantifier.NEGATIVE_SCORE * SentimentQuantifier.NEGATIVE_WEIGHT

    

    def test_neutral_score_value(self):

        """Test neutral sentiment score is exactly 0.0"""

        score = SentimentQuantifier.quantify("Neutral")

        assert score == 0.0

        assert isinstance(score, float)

    

    def test_conservative_weighting_applied(self):

        """Test that negative sentiment has conservative weighting"""

        negative_score = SentimentQuantifier.quantify("Negative")

        positive_score = SentimentQuantifier.quantify("Positive")

        

        # Negative should be weighted more heavily (1.5x)

        assert abs(negative_score) > abs(positive_score)

        assert abs(negative_score) == 1.5

        assert abs(positive_score) == 1.0

    

    def test_daily_score_mixed_sentiments(self):

        """Test daily score calculation with mixed sentiments"""

        sentiments = [

            SentimentResult(

                article_id=1,

                sentiment="Positive",

                score=1.0,

                reasoning="Good",

                analyzed_at=datetime.now()

            ),

            SentimentResult(

                article_id=2,

                sentiment="Negative",

                score=-1.5,

                reasoning="Bad",

                analyzed_at=datetime.now()

            ),

            SentimentResult(

                article_id=3,

                sentiment="Neutral",

                score=0.0,

                reasoning="Neutral",

                analyzed_at=datetime.now()

            )

        ]

        

        daily_score = SentimentQuantifier.calculate_daily_score(sentiments)

        expected = (1.0 + (-1.5) + 0.0) / 3

        assert daily_score == pytest.approx(expected)

        assert daily_score == pytest.approx(-0.1667, rel=0.01)

    

    def test_daily_score_all_positive(self):

        """Test daily score with all positive sentiments"""

        sentiments = [

            SentimentResult(

                article_id=i,

                sentiment="Positive",

                score=1.0,

                reasoning="Good",

                analyzed_at=datetime.now()

            )

            for i in range(5)

        ]

        

        daily_score = SentimentQuantifier.calculate_daily_score(sentiments)

        assert daily_score == 1.0

    

    def test_daily_score_all_negative(self):

        """Test daily score with all negative sentiments"""

        sentiments = [

            SentimentResult(

                article_id=i,

                sentiment="Negative",

                score=-1.5,

                reasoning="Bad",

                analyzed_at=datetime.now()

            )

            for i in range(5)

        ]

        

        daily_score = SentimentQuantifier.calculate_daily_score(sentiments)

        assert daily_score == -1.5

    

    def test_daily_score_empty_list(self):

        """Test daily score with empty sentiment list"""

        daily_score = SentimentQuantifier.calculate_daily_score([])

        assert daily_score == 0.0

    

    def test_daily_score_single_sentiment(self):

        """Test daily score with single sentiment"""

        sentiments = [

            SentimentResult(

                article_id=1,

                sentiment="Positive",

                score=1.0,

                reasoning="Good",

                analyzed_at=datetime.now()

            )

        ]

        

        daily_score = SentimentQuantifier.calculate_daily_score(sentiments)

        assert daily_score == 1.0

    

    def test_conservative_bias_in_average(self):

        """Test that conservative bias affects daily average"""

        # 1 positive + 1 negative should be net negative due to weighting

        sentiments = [

            SentimentResult(

                article_id=1,

                sentiment="Positive",

                score=1.0,

                reasoning="Good",

                analyzed_at=datetime.now()

            ),

            SentimentResult(

                article_id=2,

                sentiment="Negative",

                score=-1.5,

                reasoning="Bad",

                analyzed_at=datetime.now()

            )

        ]

        

        daily_score = SentimentQuantifier.calculate_daily_score(sentiments)

        assert daily_score < 0  # Should be net negative

        assert daily_score == -0.25





class TestSentimentAnalyzer:

    """Test SentimentAnalyzer class"""

    

    @pytest.fixture

    def mock_llama_client(self):

        """Create mock LlamaCppClient"""

        return Mock()

    

    @pytest.fixture

    def analyzer(self, mock_llama_client):

        """Create SentimentAnalyzer with mock client"""

        return SentimentAnalyzer(llama_client=mock_llama_client)

    

    @pytest.fixture

    def sample_article(self):

        """Create sample NewsArticle"""

        article = Mock(spec=NewsArticle)

        article.id = 1

        article.title = "Stock Market Rises on Positive Economic Data"

        article.content = "The stock market showed strong gains today..."

        article.source = "Financial Times"

        article.published_date = datetime(2025, 10, 7, 10, 30)

        return article

    

    def test_validate_sentiment_valid(self, analyzer):

        """Test sentiment validation with valid inputs"""

        assert analyzer._validate_sentiment("Positive") == "Positive"

        assert analyzer._validate_sentiment("negative") == "Negative"

        assert analyzer._validate_sentiment("NEUTRAL") == "Neutral"

    

    def test_validate_sentiment_invalid(self, analyzer):

        """Test sentiment validation with invalid inputs"""

        with pytest.raises(ValueError, match="Invalid sentiment"):

            analyzer._validate_sentiment("Unknown")

        

        with pytest.raises(ValueError, match="must be string"):

            analyzer._validate_sentiment(123)

    

    def test_analyze_article_positive(self, analyzer, mock_llama_client, sample_article):

        """Test analyzing article with positive sentiment"""

        # Mock LLM response

        mock_llama_client.generate_json.return_value = {

            "sentiment": "Positive",

            "reasoning": "Market shows strong growth indicators"

        }

        

        result = analyzer.analyze_article(sample_article)

        

        assert result.article_id == 1

        assert result.sentiment == "Positive"

        assert result.score == 1.0

        assert "growth indicators" in result.reasoning

        

        # Verify LLM was called with correct prompts

        mock_llama_client.generate_json.assert_called_once()

        call_args = mock_llama_client.generate_json.call_args

        assert "Stock Market Rises" in call_args.kwargs["prompt"]

        assert call_args.kwargs["system_prompt"] == STEP1_SYSTEM_PROMPT

    

    def test_analyze_article_negative(self, analyzer, mock_llama_client, sample_article):

        """Test analyzing article with negative sentiment"""

        mock_llama_client.generate_json.return_value = {

            "sentiment": "Negative",

            "reasoning": "Market faces significant headwinds"

        }

        

        result = analyzer.analyze_article(sample_article)

        

        assert result.sentiment == "Negative"

        assert result.score == -1.5  # Conservative weighting

        assert "headwinds" in result.reasoning

    

    def test_analyze_article_neutral(self, analyzer, mock_llama_client, sample_article):

        """Test analyzing article with neutral sentiment"""

        mock_llama_client.generate_json.return_value = {

            "sentiment": "Neutral",

            "reasoning": "Mixed signals from the market"

        }

        

        result = analyzer.analyze_article(sample_article)

        

        assert result.sentiment == "Neutral"

        assert result.score == 0.0

    

    def test_analyze_article_missing_reasoning(self, analyzer, mock_llama_client, sample_article):

        """Test handling missing reasoning in LLM response"""

        mock_llama_client.generate_json.return_value = {

            "sentiment": "Positive"

        }

        

        result = analyzer.analyze_article(sample_article)

        

        assert result.reasoning == "No reasoning provided"

    

    def test_analyze_article_invalid_response(self, analyzer, mock_llama_client, sample_article):

        """Test handling invalid LLM response"""

        mock_llama_client.generate_json.return_value = {

            "sentiment": "InvalidSentiment"

        }

        

        with pytest.raises(ValueError, match="Invalid sentiment"):

            analyzer.analyze_article(sample_article)

    

    def test_analyze_batch(self, analyzer, mock_llama_client):

        """Test batch analysis of multiple articles"""

        # Create mock articles

        articles = []

        for i in range(3):

            article = Mock(spec=NewsArticle)

            article.id = i + 1

            article.title = f"Article {i+1}"

            article.content = f"Content {i+1}"

            article.source = "Test Source"

            article.published_date = datetime.now()

            articles.append(article)

        

        # Mock LLM responses

        mock_llama_client.generate_json.side_effect = [

            {"sentiment": "Positive", "reasoning": "Good news 1"},

            {"sentiment": "Negative", "reasoning": "Bad news 2"},

            {"sentiment": "Neutral", "reasoning": "Neutral news 3"}

        ]

        

        # Mock database session

        mock_db = Mock()

        mock_db.query.return_value.filter.return_value.first.return_value = None

        

        results = analyzer.analyze_batch(articles, mock_db, skip_existing=False)

        

        assert len(results) == 3

        assert results[0].sentiment == "Positive"

        assert results[1].sentiment == "Negative"

        assert results[2].sentiment == "Neutral"

        

        # Verify database commits

        assert mock_db.commit.call_count == 3

    

    def test_analyze_batch_skip_existing(self, analyzer, mock_llama_client):

        """Test batch analysis with skip_existing=True"""

        articles = [Mock(spec=NewsArticle, id=1)]

        

        # Mock existing sentiment in database

        mock_db = Mock()

        mock_db.query.return_value.filter.return_value.first.return_value = Mock()

        

        results = analyzer.analyze_batch(articles, mock_db, skip_existing=True)

        

        assert len(results) == 0

        mock_llama_client.generate_json.assert_not_called()

    

    def test_analyze_batch_error_handling(self, analyzer, mock_llama_client):

        """Test batch analysis continues on individual errors"""

        articles = [

            Mock(spec=NewsArticle, id=1, title="Article 1", content="Content 1",

                 source="Source", published_date=datetime.now()),

            Mock(spec=NewsArticle, id=2, title="Article 2", content="Content 2",

                 source="Source", published_date=datetime.now())

        ]

        

        # First article succeeds, second fails

        mock_llama_client.generate_json.side_effect = [

            {"sentiment": "Positive", "reasoning": "Good"},

            Exception("LLM error")

        ]

        

        mock_db = Mock()

        mock_db.query.return_value.filter.return_value.first.return_value = None

        

        results = analyzer.analyze_batch(articles, mock_db, skip_existing=False)

        

        # Should have 1 successful result despite 1 error

        assert len(results) == 1

        assert results[0].sentiment == "Positive"





if __name__ == "__main__":

    pytest.main([__file__, "-v"])

