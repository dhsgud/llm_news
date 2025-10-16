"""
Prompt Templates for Market Sentiment Analysis
Defines the 3-stage prompt chain for analyzing news and generating recommendations
"""

from typing import List, Dict, Any
from datetime import datetime


# ============================================================================
# STAGE 1: Individual Article Sentiment Analysis
# ============================================================================

STEP1_SYSTEM_PROMPT = """당신은 금융 뉴스 감성 분석 전문가입니다.

주어진 뉴스 기사를 분석하고 다음 JSON 형식으로 응답하세요:
{
  "sentiment": "Positive" | "Negative" | "Neutral",
  "reasoning": "판단 근거를 2-3문장으로 설명"
}

분류 기준:
- Positive: 시장에 긍정적 영향을 미칠 것으로 예상되는 뉴스
- Negative: 시장에 부정적 영향을 미칠 것으로 예상되는 뉴스  
- Neutral: 중립적이거나 영향이 불분명한 경우

판단 기준:
- 기업 실적, 경제 지표, 정책 변화 등을 종합적으로 고려
- 단기적 시장 반응보다는 중장기적 영향에 집중
- 불확실성이 높은 경우 Neutral로 분류

중요: 반드시 유효한 JSON만 출력하고, 추가 설명이나 마크다운은 포함하지 마세요."""


def create_step1_prompt(title: str, content: str, source: str, published_date: datetime) -> str:
    """
    Create Stage 1 prompt for individual article analysis
    
    Args:
        title: Article title
        content: Article content
        source: News source
        published_date: Publication date
        
    Returns:
        Formatted prompt string
    """
    return f"""다음 뉴스 기사를 분석해주세요:

제목: {title}
출처: {source}
발행일: {published_date}

내용:
{content}

이 기사의 시장 감성을 분석하고 JSON 형식으로 응답하세요."""


# ============================================================================
# STAGE 2: Weekly Trend Aggregation
# ============================================================================

STEP2_SYSTEM_PROMPT = """당신은 주간 시장 트렌드 분석 전문가입니다.

최근 7일간의 뉴스 감성 분석 결과를 종합하여 다음 JSON 형식으로 응답하세요:
{
  "summary_text": "전반적인 시장 동향을 3-5문장으로 요약",
  "dominant_sentiment": "Positive" | "Negative" | "Neutral",
  "key_drivers": ["주요 요인 1", "주요 요인 2", "주요 요인 3"]
}

분석 시 고려사항:
- 긍정/부정 뉴스의 비율과 강도
- 일별 감성 점수의 추세 변화
- 시장에 가장 큰 영향을 미칠 것으로 예상되는 요인

전문 용어를 최소화하고 핵심 메시지에 집중하세요."""


def create_step2_prompt(sentiment_data: List[Dict[str, Any]]) -> str:
    """
    Create Stage 2 prompt for weekly trend aggregation
    
    Args:
        sentiment_data: List of sentiment analysis results with dates
        Each item should have: date, title, sentiment, score, reasoning
        
    Returns:
        Formatted prompt string
    """
    # Group by date and summarize
    daily_summaries = []
    
    for item in sentiment_data:
        date = item.get('date', 'Unknown')
        title = item.get('title', 'No title')
        sentiment = item.get('sentiment', 'Unknown')
        score = item.get('score', 0.0)
        reasoning = item.get('reasoning', '')
        
        daily_summaries.append(
            f"[{date}] {title}\n"
            f"  감성: {sentiment} (?�수: {score:.2f})\n"
            f"  근거: {reasoning}"
        )
    
    articles_text = "\n\n".join(daily_summaries)
    
    return f"""최근 7일간의 뉴스 감성 분석 결과입니다:

기간: {sentiment_data[0].get('date', 'Unknown')} ~ {sentiment_data[-1].get('date', 'Unknown')}
총 기사 수: {len(sentiment_data)}개

일별 감성 분석:
{articles_text}

이 데이터를 바탕으로 주간 시장 동향을 분석하고 JSON 형식으로 응답해주세요.
3-5문장으로 간결하게 작성하세요."""


# ============================================================================
# STAGE 3: Conservative Buy/Sell Recommendation
# ============================================================================

STEP3_SYSTEM_PROMPT = """당신은 보수적인 투자 전략 전문가입니다.

주간 트렌드 요약과 VIX 지수를 바탕으로 다음 JSON 형식으로 응답하세요:
{
  "buy_sell_ratio": "매수 비율 (0-100, 숫자만)",
  "confidence": "low" | "medium" | "high",
  "reasoning": "추천 근거를 2-3문장으로 설명"
}

보수적 투자 원칙:
- 불확실성이 높을 때는 낮은 매수 비율 권장
- VIX가 높으면 (시장 불안) 더욱 신중하게 접근
- 부정적 신호에 더 큰 가중치 부여
- 명확한 긍정 신호가 없으면 중립적 포지션 유지

매수 비율 가이드:
- 0-30: 방어적 (현금 보유 우선)
- 30-50: 중립적 (균형 잡힌 포지션)
- 50-70: 적극적 (선별적 매수)
- 70-100: 공격적 (강한 매수 신호, 매우 드물게 사용)"""


def create_step3_prompt(
    trend_summary: str,
    vix_value: float,
    vix_normalized: float,
    weekly_signal_score: float
) -> str:
    """
    Create Stage 3 prompt for conservative recommendation
    
    Args:
        trend_summary: Weekly trend summary from Stage 2
        vix_value: Current VIX value
        vix_normalized: Normalized VIX (0-1 range)
        weekly_signal_score: Calculated weekly signal score
        
    Returns:
        Formatted prompt string
    """
    # Interpret VIX level
    if vix_normalized < 0.3:
        vix_interpretation = "??�� (?�장 ?�정)"
    elif vix_normalized < 0.6:
        vix_interpretation = "보통 (?�상 변?�성)"
    else:
        vix_interpretation = "?�음 (?�장 불안)"
    
    # Interpret signal score
    if weekly_signal_score > 3.0:
        signal_interpretation = "강한 긍정"
    elif weekly_signal_score > 0.5:
        signal_interpretation = "약한 긍정"
    elif weekly_signal_score > -0.5:
        signal_interpretation = "중립"
    elif weekly_signal_score > -3.0:
        signal_interpretation = "약한 부정"
    else:
        signal_interpretation = "강한 부정"
    
    return f"""다음 정보를 바탕으로 투자 추천을 제공해주세요:

=== 주간 트렌드 요약 ===
{trend_summary}

=== 시장 변동성 지표 ===
현재 VIX: {vix_value:.2f}
VIX 수준: {vix_interpretation}
정규화 VIX: {vix_normalized:.2f} (0=매우 낮음, 1=매우 높음)

=== 주간 감성 점수 ===
점수: {weekly_signal_score:.2f}
해석: {signal_interpretation}

보수적 투자 원칙을 적용하여 적절한 매수/매도 비율을 추천하고,
JSON 형식으로만 응답하세요."""


# ============================================================================
# Utility Functions
# ============================================================================

def validate_step1_response(response: Dict[str, Any]) -> bool:
    """
    Validate Stage 1 response format
    
    Args:
        response: Parsed JSON response
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["sentiment", "reasoning"]
    valid_sentiments = ["Positive", "Negative", "Neutral"]
    
    if not all(field in response for field in required_fields):
        return False
    
    if response["sentiment"] not in valid_sentiments:
        return False
    
    if not isinstance(response["reasoning"], str) or not response["reasoning"].strip():
        return False
    
    return True


def validate_step3_response(response: Dict[str, Any]) -> bool:
    """
    Validate Stage 3 response format
    
    Args:
        response: Parsed JSON response
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["buy_sell_ratio", "confidence", "reasoning"]
    valid_confidence = ["low", "medium", "high"]
    
    if not all(field in response for field in required_fields):
        return False
    
    ratio = response["buy_sell_ratio"]
    if not isinstance(ratio, (int, float)) or not (0 <= ratio <= 100):
        return False
    
    if response["confidence"] not in valid_confidence:
        return False
    
    if not isinstance(response["reasoning"], str) or not response["reasoning"].strip():
        return False
    
    return True
