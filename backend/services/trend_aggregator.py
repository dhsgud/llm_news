"""

Trend Aggregator Module

Handles weekly trend aggregation and summary generation using LLM

"""



import logging

from datetime import datetime, timedelta

from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session



from services.llm_client import LlamaCppClient, LlamaCppClientError

from models import SentimentAnalysis, NewsArticle, SentimentResult



logger = logging.getLogger(__name__)





# Step 2 Prompt Template

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





STEP2_USER_PROMPT_TEMPLATE = """최근 7일간의 뉴스 감성 분석 결과입니다:

기간: {start_date} ~ {end_date}
총 기사 수: {total_count}개

감성 분포:
- 긍정: {positive_count}개 (평균 점수: {positive_avg:+.2f})
- 부정: {negative_count}개 (평균 점수: {negative_avg:+.2f})
- 중립: {neutral_count}개

일별 평균 점수:
{daily_scores}

주요 뉴스 샘플:
{news_samples}

이 데이터를 바탕으로 주간 시장 동향을 분석하고 JSON 형식으로 응답해주세요."""





class TrendSummary(BaseModel):

    """

    Weekly trend summary result

    """

    summary_text: str = Field(..., description="Overall market trend summary")

    dominant_sentiment: str = Field(..., description="Dominant sentiment: Positive, Negative, or Neutral")

    key_drivers: List[str] = Field(default_factory=list, description="Key market drivers")

    period_start: datetime = Field(..., description="Analysis period start date")

    period_end: datetime = Field(..., description="Analysis period end date")

    total_articles: int = Field(..., description="Total number of articles analyzed")

    average_score: float = Field(..., description="Average sentiment score for the period")







class TrendAggregator:

    """

    Aggregates weekly sentiment data and generates trend summary

    

    Implements Step 2 of the 3-step prompt chain:

    - Collects 7 days of sentiment data

    - Aggregates statistics

    - Generates comprehensive trend summary using LLM

    """

    

    def __init__(self, llama_client: Optional[LlamaCppClient] = None):

        """

        Initialize trend aggregator

        

        Args:

            llama_client: LlamaCppClient instance (creates new one if not provided)

        """

        self.llama_client = llama_client or LlamaCppClient()

        logger.info("TrendAggregator initialized")

    

    def aggregate_weekly_trend(

        self,

        db: Session,

        days: int = 7,

        temperature: float = 0.5,

        max_tokens: int = 1000

    ) -> TrendSummary:

        """

        Aggregate weekly trend from sentiment data

        

        Collects sentiment data from the last N days and generates

        a comprehensive trend summary using Step 2 LLM prompt.

        

        Args:

            db: Database session

            days: Number of days to analyze (default: 7)

            temperature: LLM temperature for generation

            max_tokens: Maximum tokens for LLM response

            

        Returns:

            TrendSummary with aggregated analysis

            

        Raises:

            LlamaCppClientError: If LLM request fails

            ValueError: If insufficient data or invalid response

        """

        logger.info(f"Starting weekly trend aggregation for last {days} days")

        

        # Calculate date range

        end_date = datetime.now()

        start_date = end_date - timedelta(days=days)

        

        # Fetch sentiment data from database

        sentiments = self._fetch_sentiments(db, start_date, end_date)

        

        if not sentiments:

            raise ValueError(

                f"No sentiment data found for period {start_date.date()} to {end_date.date()}"

            )

        

        logger.info(f"Found {len(sentiments)} sentiment analyses to aggregate")

        

        # Calculate statistics

        stats = self._calculate_statistics(sentiments)

        

        # Fetch sample news articles for context

        news_samples = self._fetch_news_samples(db, sentiments, limit=10)

        

        # Build user prompt with aggregated data

        user_prompt = self._build_prompt(

            start_date=start_date,

            end_date=end_date,

            stats=stats,

            news_samples=news_samples

        )

        

        try:

            # Call LLM with Step 2 prompt

            response_json = self.llama_client.generate_json(

                prompt=user_prompt,

                system_prompt=STEP2_SYSTEM_PROMPT,

                temperature=temperature,

                max_tokens=max_tokens

            )

            

            # Parse and validate response

            summary_text = response_json.get("summary_text", "")

            dominant_sentiment = response_json.get("dominant_sentiment", "Neutral")

            key_drivers = response_json.get("key_drivers", [])

            

            if not summary_text:

                raise ValueError("LLM response missing summary_text")

            

            # Create TrendSummary object

            trend_summary = TrendSummary(

                summary_text=summary_text,

                dominant_sentiment=dominant_sentiment,

                key_drivers=key_drivers,

                period_start=start_date,

                period_end=end_date,

                total_articles=stats["total_count"],

                average_score=stats["average_score"]

            )

            

            logger.info(

                f"Weekly trend aggregated: {dominant_sentiment} sentiment, "

                f"{len(key_drivers)} key drivers identified"

            )

            

            return trend_summary

            

        except LlamaCppClientError as e:

            logger.error(f"LLM request failed during trend aggregation: {e}")

            raise

            

        except (KeyError, ValueError) as e:

            logger.error(f"Invalid LLM response format: {e}")

            raise ValueError(f"Invalid trend aggregation response: {str(e)}") from e



    

    def _fetch_sentiments(

        self,

        db: Session,

        start_date: datetime,

        end_date: datetime

    ) -> List[SentimentAnalysis]:

        """

        Fetch sentiment analyses from database for date range

        

        Args:

            db: Database session

            start_date: Start of date range

            end_date: End of date range

            

        Returns:

            List of SentimentAnalysis objects

        """

        sentiments = db.query(SentimentAnalysis).filter(

            SentimentAnalysis.analyzed_at >= start_date,

            SentimentAnalysis.analyzed_at <= end_date

        ).order_by(SentimentAnalysis.analyzed_at.asc()).all()

        

        return sentiments

    

    def _calculate_statistics(

        self,

        sentiments: List[SentimentAnalysis]

    ) -> Dict[str, Any]:

        """

        Calculate statistical summary of sentiment data

        

        Args:

            sentiments: List of SentimentAnalysis objects

            

        Returns:

            Dictionary with statistics

        """

        total_count = len(sentiments)

        

        # Count by sentiment type

        positive_sentiments = [s for s in sentiments if s.sentiment == "Positive"]

        negative_sentiments = [s for s in sentiments if s.sentiment == "Negative"]

        neutral_sentiments = [s for s in sentiments if s.sentiment == "Neutral"]

        

        positive_count = len(positive_sentiments)

        negative_count = len(negative_sentiments)

        neutral_count = len(neutral_sentiments)

        

        # Calculate average scores

        positive_avg = (

            sum(s.score for s in positive_sentiments) / positive_count

            if positive_count > 0 else 0.0

        )

        negative_avg = (

            sum(s.score for s in negative_sentiments) / negative_count

            if negative_count > 0 else 0.0

        )

        

        # Calculate overall average

        average_score = sum(s.score for s in sentiments) / total_count

        

        # Group by day for daily scores

        daily_scores = self._calculate_daily_scores(sentiments)

        

        return {

            "total_count": total_count,

            "positive_count": positive_count,

            "negative_count": negative_count,

            "neutral_count": neutral_count,

            "positive_avg": positive_avg,

            "negative_avg": negative_avg,

            "average_score": average_score,

            "daily_scores": daily_scores

        }

    

    def _calculate_daily_scores(

        self,

        sentiments: List[SentimentAnalysis]

    ) -> Dict[str, float]:

        """

        Calculate average sentiment score for each day

        

        Args:

            sentiments: List of SentimentAnalysis objects

            

        Returns:

            Dictionary mapping date string to average score

        """

        daily_data: Dict[str, List[float]] = {}

        

        for sentiment in sentiments:

            date_key = sentiment.analyzed_at.strftime("%Y-%m-%d")

            if date_key not in daily_data:

                daily_data[date_key] = []

            daily_data[date_key].append(sentiment.score)

        

        # Calculate averages

        daily_scores = {

            date: sum(scores) / len(scores)

            for date, scores in daily_data.items()

        }

        

        return daily_scores



    

    def _fetch_news_samples(

        self,

        db: Session,

        sentiments: List[SentimentAnalysis],

        limit: int = 10

    ) -> List[Dict[str, Any]]:

        """

        Fetch sample news articles for context

        

        Selects a diverse sample including positive, negative, and neutral articles.

        

        Args:

            db: Database session

            sentiments: List of SentimentAnalysis objects

            limit: Maximum number of samples to fetch

            

        Returns:

            List of dictionaries with article info

        """

        # Get article IDs from sentiments

        article_ids = [s.article_id for s in sentiments]

        

        if not article_ids:

            return []

        

        # Fetch articles

        articles = db.query(NewsArticle).filter(

            NewsArticle.id.in_(article_ids)

        ).limit(limit).all()

        

        # Create sentiment lookup

        sentiment_map = {s.article_id: s for s in sentiments}

        

        # Build sample data

        samples = []

        for article in articles:

            sentiment = sentiment_map.get(article.id)

            if sentiment:

                samples.append({

                    "title": article.title,

                    "sentiment": sentiment.sentiment,

                    "score": sentiment.score,

                    "date": article.published_date.strftime("%Y-%m-%d"),

                    "reasoning": sentiment.reasoning[:100] if sentiment.reasoning else ""

                })

        

        return samples

    

    def _build_prompt(

        self,

        start_date: datetime,

        end_date: datetime,

        stats: Dict[str, Any],

        news_samples: List[Dict[str, Any]]

    ) -> str:

        """

        Build Step 2 user prompt with aggregated data

        

        Args:

            start_date: Analysis period start

            end_date: Analysis period end

            stats: Statistical summary

            news_samples: Sample news articles

            

        Returns:

            Formatted prompt string

        """

        # Format daily scores

        daily_scores_text = "\n".join([

            f"  {date}: {score:+.2f}"

            for date, score in sorted(stats["daily_scores"].items())

        ])

        

        # Format news samples

        news_samples_text = "\n\n".join([

            f"[{sample['date']}] {sample['sentiment']} ({sample['score']:+.2f})\n"

            f"제목: {sample['title']}\n"

            f"근거: {sample['reasoning']}"

            for sample in news_samples[:5]  # Limit to top 5 for prompt length

        ])

        

        if not news_samples_text:

            news_samples_text = "(샘플 없음)"

        

        prompt = STEP2_USER_PROMPT_TEMPLATE.format(

            start_date=start_date.strftime("%Y-%m-%d"),

            end_date=end_date.strftime("%Y-%m-%d"),

            total_count=stats["total_count"],

            positive_count=stats["positive_count"],

            positive_avg=stats["positive_avg"],

            negative_count=stats["negative_count"],

            negative_avg=stats["negative_avg"],

            neutral_count=stats["neutral_count"],

            daily_scores=daily_scores_text,

            news_samples=news_samples_text

        )

        

        return prompt

    

    def close(self):

        """Close LLM client connection"""

        if self.llama_client:

            self.llama_client.close()

            logger.debug("TrendAggregator closed")

    

    def __enter__(self):

        """Context manager entry"""

        return self

    

    def __exit__(self, exc_type, exc_val, exc_tb):

        """Context manager exit"""

        self.close()

