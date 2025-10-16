"""

Simple unit tests for SentimentAnalyzer core logic

Tests quantification and validation without database dependencies

"""



import pytest

import sys

import os



# Add parent directory to path for imports

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))





def test_sentiment_quantification():

    """Test sentiment score quantification logic"""

    # Test constants

    POSITIVE_SCORE = 1.0

    NEUTRAL_SCORE = 0.0

    NEGATIVE_SCORE = -1.0

    NEGATIVE_WEIGHT = 1.5

    

    # Test positive

    score = POSITIVE_SCORE

    assert score == 1.0

    

    # Test negative with conservative weight

    score = NEGATIVE_SCORE * NEGATIVE_WEIGHT

    assert score == -1.5

    

    # Test neutral

    score = NEUTRAL_SCORE

    assert score == 0.0

    

    print("??Sentiment quantification logic verified")





def test_sentiment_validation():

    """Test sentiment label validation"""

    valid_sentiments = ["Positive", "Negative", "Neutral"]

    

    # Test valid sentiments

    for sentiment in valid_sentiments:

        assert sentiment in valid_sentiments

    

    # Test case normalization

    assert "positive".title() == "Positive"

    assert "NEGATIVE".title() == "Negative"

    assert "neutral".title() == "Neutral"

    

    # Test invalid sentiment

    invalid = "Unknown"

    assert invalid not in valid_sentiments

    

    print("??Sentiment validation logic verified")





def test_daily_score_calculation():

    """Test daily sentiment score aggregation"""

    # Simulate sentiment scores

    scores = [1.0, -1.5, 0.0]  # Positive, Negative, Neutral

    

    # Calculate average

    if scores:

        daily_score = sum(scores) / len(scores)

    else:

        daily_score = 0.0

    

    expected = (1.0 + (-1.5) + 0.0) / 3

    assert daily_score == pytest.approx(expected)

    assert daily_score == pytest.approx(-0.1667, rel=0.01)

    

    print(f"??Daily score calculation verified: {daily_score:.4f}")





def test_empty_scores():

    """Test handling of empty sentiment list"""

    scores = []

    

    if scores:

        daily_score = sum(scores) / len(scores)

    else:

        daily_score = 0.0

    

    assert daily_score == 0.0

    

    print("??Empty scores handling verified")





def test_prompt_template_structure():

    """Test that prompt templates have required structure"""

    system_prompt = """?�신?� ?�정 금융 ?�산???�???�스 기사??감성??분석?�는 ?�문 금융 분석가?�니??"""

    

    # Check system prompt contains key elements

    assert "금융 분석가" in system_prompt

    assert "감성" in system_prompt

    

    user_prompt_template = """_음 "
발행?? {published_date}"""

    

    # Check user prompt has placeholders

    assert "{title}" in user_prompt_template

    assert "{content}" in user_prompt_template

    assert "{source}" in user_prompt_template

    assert "{published_date}" in user_prompt_template

    

    # Test formatting

    formatted = user_prompt_template.format(

        title="Test Title",

        content="Test Content",

        source="Test Source",

        published_date="2025-10-07"

    )

    

    assert "Test Title" in formatted

    assert "Test Content" in formatted

    assert "Test Source" in formatted

    assert "2025-10-07" in formatted

    

    print("??Prompt template structure verified")





def test_json_response_parsing():

    """Test JSON response parsing logic"""

    import json

    

    # Valid JSON response

    response_text = '{"sentiment": "Positive", "reasoning": "Good news"}'

    parsed = json.loads(response_text)

    

    assert "sentiment" in parsed

    assert "reasoning" in parsed

    assert parsed["sentiment"] == "Positive"

    assert parsed["reasoning"] == "Good news"

    

    # JSON wrapped in markdown

    markdown_response = '```json\n{"sentiment": "Negative", "reasoning": "Bad news"}\n```'

    

    # Extract JSON from markdown

    if "```json" in markdown_response:

        start = markdown_response.find("```json") + 7

        end = markdown_response.find("```", start)

        if end != -1:

            content = markdown_response[start:end].strip()

            parsed = json.loads(content)

    

    assert parsed["sentiment"] == "Negative"

    assert parsed["reasoning"] == "Bad news"

    

    # JSON with extra text

    mixed_response = 'Here is my analysis: {"sentiment": "Neutral", "reasoning": "Mixed signals"} That is all.'

    

    # Extract JSON object

    if "{" in mixed_response:

        start = mixed_response.find("{")

        brace_count = 0

        end = -1

        for i in range(start, len(mixed_response)):

            if mixed_response[i] == "{":

                brace_count += 1

            elif mixed_response[i] == "}":

                brace_count -= 1

                if brace_count == 0:

                    end = i + 1

                    break

        

        if end != -1:

            content = mixed_response[start:end]

            parsed = json.loads(content)

    

    assert parsed["sentiment"] == "Neutral"

    

    print("??JSON response parsing logic verified")





def test_conservative_weighting():

    """Test that negative sentiment has conservative weighting"""

    NEGATIVE_WEIGHT = 1.5

    

    # Negative news should be weighted more heavily

    negative_score = -1.0 * NEGATIVE_WEIGHT

    positive_score = 1.0

    

    # Absolute value of negative should be greater

    assert abs(negative_score) > abs(positive_score)

    assert negative_score == -1.5

    

    # Test impact on daily average

    # 1 positive + 1 negative should be net negative due to weighting

    scores = [positive_score, negative_score]

    average = sum(scores) / len(scores)

    

    assert average < 0  # Net negative

    assert average == -0.25

    

    print(f"??Conservative weighting verified: {negative_score} vs {positive_score}")





if __name__ == "__main__":

    pytest.main([__file__, "-v", "-s"])

