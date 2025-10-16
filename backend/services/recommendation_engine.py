"""

Recommendation Engine Module

Generates conservative investment recommendations using LLM

"""



import logging

from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from datetime import datetime



from services.llm_client import LlamaCppClient, LlamaCppClientError

from services.trend_aggregator import TrendSummary

from services.signal_generator import VIXFetcher, SignalCalculator



logger = logging.getLogger(__name__)





# Step 3 Prompt Template

STEP3_SYSTEM_PROMPT = """당신은 보수적인 투자 자문가입니다.
주간 트렌드 요약과 VIX 데이터를 바탕으로 신중한 투자 추천을 제공하세요.

다음 형식으로 JSON 응답을 제공하세요:
{
  "recommendation": "매수/매도 추천을 2-3문장으로 설명",
  "confidence": "low" | "medium" | "high",
  "risk_assessment": "현재 시장 리스크 평가",
  "key_considerations": ["고려사항 1", "고려사항 2", "고려사항 3"]
}

판단 기준:
- 보수적 접근: 불확실성이 높으면 매도 비중 증가
- VIX 고려: 변동성이 높으면 리스크 회피
- 명확한 긍정 신호가 있을 때만 강한 매수 추천"""





STEP3_USER_PROMPT_TEMPLATE = """다음 정보를 바탕으로 투자 추천을 제공해주세요:

## 주간 트렌드 분석
- 기간: {period_start} ~ {period_end}
- 분석 기사 수: {total_articles}개
- 평균 감성 점수: {average_score:.2f}
- 주요 감성: {dominant_sentiment}

트렌드 요약:
{summary_text}

주요 동인:
{key_drivers}

## 시장 변동성 (VIX)
- 현재 VIX: {vix_raw:.2f}
- 정규화 VIX: {vix_normalized:.2f}
- 변동성 수준: {volatility_level}

## 계산된 신호
- 주간 신호 점수: {signal_score:.2f}
- 매수/매도 비율: {calculated_ratio}

이 정보를 종합하여 보수적인 투자 추천을 JSON 형식으로 제공해주세요."""





class Recommendation(BaseModel):

    """

    Investment recommendation result

    """

    buy_sell_ratio: int = Field(..., ge=0, le=100, description="Buy/sell ratio (0-100)")

    recommendation: str = Field(..., description="Investment recommendation text")

    confidence: str = Field(..., description="Confidence level: low, medium, or high")

    risk_assessment: str = Field(..., description="Current market risk assessment")

    key_considerations: list[str] = Field(default_factory=list, description="Key considerations for the recommendation")

    trend_summary: str = Field(..., description="Weekly trend summary")

    vix: float = Field(..., description="Current VIX value")

    vix_normalized: float = Field(..., description="Normalized VIX (0-1)")

    signal_score: float = Field(..., description="Raw weekly signal score")

    last_updated: datetime = Field(default_factory=datetime.now, description="Timestamp of recommendation")





class RecommendationEngine:

    """

    Generates conservative investment recommendations

    

    Implements Step 3 of the 3-step prompt chain:

    - Takes trend summary and VIX data

    - Calculates signal score and ratio

    - Generates conservative recommendation using LLM with high reasoning

    """

    

    def __init__(

        self,

        llama_client: Optional[LlamaCppClient] = None,

        vix_fetcher: Optional[VIXFetcher] = None,

        signal_calculator: Optional[SignalCalculator] = None

    ):

        """

        Initialize recommendation engine

        

        Args:

            llama_client: LlamaCppClient instance (creates new one if not provided)

            vix_fetcher: VIXFetcher instance (creates new one if not provided)

            signal_calculator: SignalCalculator instance (creates new one if not provided)

        """

        self.llama_client = llama_client or LlamaCppClient()

        self.vix_fetcher = vix_fetcher or VIXFetcher(api_source="mock")

        self.signal_calculator = signal_calculator or SignalCalculator(vix_fetcher=self.vix_fetcher)

        

        logger.info("RecommendationEngine initialized")



    

    def generate_recommendation(

        self,

        trend: TrendSummary,

        vix: Optional[float] = None,

        temperature: float = 0.7,

        max_tokens: int = 1500

    ) -> Recommendation:

        """

        Generate conservative investment recommendation

        

        Uses Step 3 prompt with Reasoning: high level for deep analysis.

        Integrates trend summary, VIX data, and signal calculation.

        

        Args:

            trend: TrendSummary from TrendAggregator

            vix: Optional VIX value (fetches if not provided)

            temperature: LLM temperature for generation

            max_tokens: Maximum tokens for LLM response

            

        Returns:

            Recommendation with buy/sell ratio and detailed analysis

            

        Raises:

            LlamaCppClientError: If LLM request fails

            ValueError: If invalid response or data

        """

        logger.info("Generating investment recommendation")

        

        # Fetch VIX if not provided

        if vix is None:

            vix = self.vix_fetcher.get_current_vix()

        

        vix_normalized = self.vix_fetcher.normalize_vix(vix)

        

        # Calculate signal score from trend data

        # Use average score as proxy for daily scores

        daily_scores = [trend.average_score] * 7  # Simplified for now

        signal_score = self.signal_calculator.calculate_weekly_signal(

            daily_scores,

            vix_normalized

        )

        

        # Calculate buy/sell ratio

        calculated_ratio = self.signal_calculator.normalize_to_ratio(signal_score)

        

        # Determine volatility level

        volatility_level = self._assess_volatility(vix)

        

        # Build user prompt

        user_prompt = self._build_prompt(

            trend=trend,

            vix_raw=vix,

            vix_normalized=vix_normalized,

            signal_score=signal_score,

            calculated_ratio=calculated_ratio,

            volatility_level=volatility_level

        )

        

        try:

            # Call LLM with Step 3 prompt (high reasoning)

            response_json = self.llama_client.generate_json(

                prompt=user_prompt,

                system_prompt=STEP3_SYSTEM_PROMPT,

                temperature=temperature,

                max_tokens=max_tokens

            )

            

            # Parse and validate response

            recommendation_text = response_json.get("recommendation", "")

            confidence = response_json.get("confidence", "medium")

            risk_assessment = response_json.get("risk_assessment", "")

            key_considerations = response_json.get("key_considerations", [])

            

            if not recommendation_text:

                raise ValueError("LLM response missing recommendation text")

            

            # Validate confidence level

            if confidence not in ["low", "medium", "high"]:

                logger.warning(f"Invalid confidence level '{confidence}', defaulting to 'medium'")

                confidence = "medium"

            

            # Create Recommendation object

            recommendation = Recommendation(

                buy_sell_ratio=calculated_ratio,

                recommendation=recommendation_text,

                confidence=confidence,

                risk_assessment=risk_assessment,

                key_considerations=key_considerations,

                trend_summary=trend.summary_text,

                vix=vix,

                vix_normalized=vix_normalized,

                signal_score=signal_score,

                last_updated=datetime.now()

            )

            

            logger.info(

                f"Recommendation generated: ratio={calculated_ratio}, "

                f"confidence={confidence}, VIX={vix:.2f}"

            )

            

            return recommendation

            

        except LlamaCppClientError as e:

            logger.error(f"LLM request failed during recommendation generation: {e}")

            raise

            

        except (KeyError, ValueError) as e:

            logger.error(f"Invalid LLM response format: {e}")

            raise ValueError(f"Invalid recommendation response: {str(e)}") from e

    

    def _assess_volatility(self, vix: float) -> str:

        """

        Assess volatility level based on VIX value

        

        Args:

            vix: VIX value

            

        Returns:

            Volatility level description

        """

        if vix < 15:

            return "낮음 (Low) - 안정적인 시장"

        elif vix < 20:

            return "보통 (Normal) - 정상적인 변동성"

        elif vix < 30:

            return "높음 (Elevated) - 불확실성 증가"

        else:

            return "매우 높음 (High) - 시장 공포 수준"

    

    def _build_prompt(

        self,

        trend: TrendSummary,

        vix_raw: float,

        vix_normalized: float,

        signal_score: float,

        calculated_ratio: int,

        volatility_level: str

    ) -> str:

        """

        Build Step 3 user prompt with all analysis data

        

        Args:

            trend: TrendSummary object

            vix_raw: Raw VIX value

            vix_normalized: Normalized VIX (0-1)

            signal_score: Raw signal score

            calculated_ratio: Calculated buy/sell ratio

            volatility_level: Volatility assessment

            

        Returns:

            Formatted prompt string

        """

        # Format key drivers

        key_drivers_text = "\n".join([

            f"  - {driver}"

            for driver in trend.key_drivers

        ])

        

        if not key_drivers_text:

            key_drivers_text = "  (식별된 주요 동인 없음)"

        

        prompt = STEP3_USER_PROMPT_TEMPLATE.format(

            period_start=trend.period_start.strftime("%Y-%m-%d"),

            period_end=trend.period_end.strftime("%Y-%m-%d"),

            total_articles=trend.total_articles,

            average_score=trend.average_score,

            dominant_sentiment=trend.dominant_sentiment,

            summary_text=trend.summary_text,

            key_drivers=key_drivers_text,

            vix_raw=vix_raw,

            vix_normalized=vix_normalized,

            volatility_level=volatility_level,

            signal_score=signal_score,

            calculated_ratio=calculated_ratio

        )

        

        return prompt

    

    def close(self):

        """Close LLM client connection"""

        if self.llama_client:

            self.llama_client.close()

            logger.debug("RecommendationEngine closed")

    

    def __enter__(self):

        """Context manager entry"""

        return self

    

    def __exit__(self, exc_type, exc_val, exc_tb):

        """Context manager exit"""

        self.close()

