"""

Sentiment Analyzer Module

Handles sentiment analysis of news articles using LLM

"""



import json

import logging

from datetime import datetime

from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session



from services.llm_client import LlamaCppClient, LlamaCppClientError

from models import (

    NewsArticle,

    SentimentAnalysis,

    SentimentAnalysisCreate,

    SentimentResult,

    SentimentType

)



logger = logging.getLogger(__name__)





# Prompt templates for sentiment analysis

STEP1_SYSTEM_PROMPT = """당신은 금융 뉴스 분석 전문가입니다.
주어진 뉴스 기사를 읽고 시장에 미치는 영향을 분석하세요.

다음 형식으로 JSON 응답을 제공하세요:
{
  "sentiment": "Positive" | "Negative" | "Neutral",
  "reasoning": "판단 근거를 2-3문장으로 설명"
}

분류 기준:
- Positive: 시장에 긍정적 영향을 미치는 뉴스 (주가 상승 요인)
- Negative: 시장에 부정적 영향을 미치는 뉴스 (주가 하락 요인)
- Neutral: 중립적이거나 영향이 불분명한 경우"""





STEP1_USER_PROMPT_TEMPLATE = """다음 뉴스 기사를 분석해주세요:

제목: {title}
내용: {content}
출처: {source}
발행일: {published_date}

이 기사의 감성을 분석하고 JSON 형식으로 답변해주세요."""





class SentimentQuantifier:

    """

    Sentiment score quantification with conservative bias

    """

    POSITIVE_SCORE = 1.0

    NEUTRAL_SCORE = 0.0

    NEGATIVE_SCORE = -1.0

    NEGATIVE_WEIGHT = 1.5  # Conservative bias: negative news weighted more heavily

    

    @classmethod

    def quantify(cls, sentiment: SentimentType) -> float:

        """

        Convert sentiment label to quantified score

        

        Args:

            sentiment: Sentiment label ('Positive', 'Negative', 'Neutral')

            

        Returns:

            Quantified score (-1.5 for Negative, 0.0 for Neutral, 1.0 for Positive)

        """

        if sentiment == "Positive":

            return cls.POSITIVE_SCORE

        elif sentiment == "Negative":

            return cls.NEGATIVE_SCORE * cls.NEGATIVE_WEIGHT  # -1.5

        else:  # Neutral

            return cls.NEUTRAL_SCORE

    

    @classmethod

    def calculate_daily_score(cls, sentiments: List[SentimentResult]) -> float:

        """

        Calculate aggregated daily sentiment score

        

        Args:

            sentiments: List of sentiment results for a day

            

        Returns:

            Average sentiment score for the day

        """

        if not sentiments:

            return 0.0

        

        total_score = sum(s.score for s in sentiments)

        return total_score / len(sentiments)





class SentimentAnalyzer:

    """

    Analyzes sentiment of news articles using LLM

    

    Implements Step 1 of the 3-step prompt chain:

    - Individual article analysis

    - JSON response parsing

    - Sentiment score quantification with conservative weighting

    """

    

    def __init__(self, llama_client: Optional[LlamaCppClient] = None):

        """

        Initialize sentiment analyzer

        

        Args:

            llama_client: LlamaCppClient instance (creates new one if not provided)

        """

        self.llama_client = llama_client or LlamaCppClient()

        self.quantifier = SentimentQuantifier()

        

        logger.info("SentimentAnalyzer initialized")

    

    def analyze_article(

        self,

        article: NewsArticle,

        temperature: float = 0.3,

        max_tokens: int = 500

    ) -> SentimentResult:

        """

        Analyze sentiment of a single news article

        

        Uses Step 1 prompt with Reasoning: medium level for efficiency.

        

        Args:

            article: NewsArticle object to analyze

            temperature: LLM temperature (lower = more deterministic)

            max_tokens: Maximum tokens for LLM response

            

        Returns:

            SentimentResult with sentiment, score, and reasoning

            

        Raises:

            LlamaCppClientError: If LLM request fails

            ValueError: If LLM response format is invalid

        """

        logger.info(f"Analyzing article {article.id}: {article.title[:50]}...")

        

        # Build user prompt with article details

        user_prompt = STEP1_USER_PROMPT_TEMPLATE.format(

            title=article.title,

            content=article.content[:2000],  # Limit content length to avoid token overflow

            source=article.source,

            published_date=article.published_date.strftime("%Y-%m-%d %H:%M")

        )

        

        try:

            # Call LLM with JSON output

            response_json = self.llama_client.generate_json(

                prompt=user_prompt,

                system_prompt=STEP1_SYSTEM_PROMPT,

                temperature=temperature,

                max_tokens=max_tokens

            )

            

            # Parse and validate response

            sentiment_label = self._validate_sentiment(response_json.get("sentiment"))

            reasoning = response_json.get("reasoning", "")

            

            if not reasoning:

                logger.warning(f"Article {article.id}: No reasoning provided in LLM response")

                reasoning = "No reasoning provided"

            

            # Quantify sentiment score with conservative weighting

            score = self.quantifier.quantify(sentiment_label)

            

            result = SentimentResult(

                article_id=article.id,

                sentiment=sentiment_label,

                score=score,

                reasoning=reasoning,

                analyzed_at=datetime.now()

            )

            

            logger.info(

                f"Article {article.id} analyzed: {sentiment_label} "

                f"(score: {score:.2f})"

            )

            

            return result

            

        except LlamaCppClientError as e:

            logger.error(f"LLM request failed for article {article.id}: {e}")

            raise

            

        except (KeyError, ValueError) as e:

            logger.error(

                f"Invalid LLM response format for article {article.id}: {e}"

            )

            raise ValueError(f"Invalid sentiment analysis response: {str(e)}") from e

    

    def _validate_sentiment(self, sentiment: Any) -> SentimentType:

        """

        Validate and normalize sentiment label

        

        Args:

            sentiment: Sentiment value from LLM response

            

        Returns:

            Validated SentimentType

            

        Raises:

            ValueError: If sentiment is invalid

        """

        if not isinstance(sentiment, str):

            raise ValueError(f"Sentiment must be string, got {type(sentiment)}")

        

        # Normalize to title case

        sentiment = sentiment.strip().title()

        

        valid_sentiments = ["Positive", "Negative", "Neutral"]

        if sentiment not in valid_sentiments:

            raise ValueError(

                f"Invalid sentiment '{sentiment}'. "

                f"Must be one of: {', '.join(valid_sentiments)}"

            )

        

        return sentiment  # type: ignore

    

    def analyze_batch(

        self,

        articles: List[NewsArticle],

        db: Session,

        skip_existing: bool = True

    ) -> List[SentimentResult]:

        """

        Analyze sentiment for multiple articles

        

        Processes articles sequentially and stores results in database.

        

        Args:

            articles: List of NewsArticle objects to analyze

            db: Database session for storing results

            skip_existing: If True, skip articles that already have sentiment analysis

            

        Returns:

            List of SentimentResult objects

        """

        logger.info(f"Starting batch analysis of {len(articles)} articles")

        

        results = []

        analyzed_count = 0

        skipped_count = 0

        error_count = 0

        

        for article in articles:

            try:

                # Check if article already has sentiment analysis

                if skip_existing:

                    existing = db.query(SentimentAnalysis).filter(

                        SentimentAnalysis.article_id == article.id

                    ).first()

                    

                    if existing:

                        logger.debug(f"Skipping article {article.id}: already analyzed")

                        skipped_count += 1

                        continue

                

                # Analyze article

                result = self.analyze_article(article)

                results.append(result)

                

                # Store in database

                self._save_to_db(result, db)

                analyzed_count += 1

                

            except Exception as e:

                logger.error(

                    f"Failed to analyze article {article.id}: {e}",

                    exc_info=True

                )

                error_count += 1

                continue

        

        logger.info(

            f"Batch analysis completed: {analyzed_count} analyzed, "

            f"{skipped_count} skipped, {error_count} errors"

        )

        

        return results

    

    def _save_to_db(self, result: SentimentResult, db: Session) -> SentimentAnalysis:

        """

        Save sentiment analysis result to database

        

        Args:

            result: SentimentResult to save

            db: Database session

            

        Returns:

            Created SentimentAnalysis database object

        """

        sentiment_data = SentimentAnalysisCreate(

            article_id=result.article_id,

            sentiment=result.sentiment,

            score=result.score,

            reasoning=result.reasoning

        )

        

        db_sentiment = SentimentAnalysis(**sentiment_data.model_dump())

        db.add(db_sentiment)

        db.commit()

        db.refresh(db_sentiment)

        

        logger.debug(f"Saved sentiment analysis {db_sentiment.id} to database")

        

        return db_sentiment

    

    def get_recent_sentiments(

        self,

        db: Session,

        days: int = 7

    ) -> List[SentimentResult]:

        """

        Retrieve recent sentiment analysis results

        

        Args:

            db: Database session

            days: Number of days to look back

            

        Returns:

            List of SentimentResult objects

        """

        from datetime import timedelta

        

        cutoff_date = datetime.now() - timedelta(days=days)

        

        sentiments = db.query(SentimentAnalysis).filter(

            SentimentAnalysis.analyzed_at >= cutoff_date

        ).order_by(SentimentAnalysis.analyzed_at.desc()).all()

        

        results = [

            SentimentResult(

                article_id=s.article_id,

                sentiment=s.sentiment,

                score=s.score,

                reasoning=s.reasoning or "",

                analyzed_at=s.analyzed_at

            )

            for s in sentiments

        ]

        

        logger.info(f"Retrieved {len(results)} sentiment results from last {days} days")

        

        return results

    

    def close(self):

        """Close LLM client connection"""

        if self.llama_client:

            self.llama_client.close()

            logger.debug("SentimentAnalyzer closed")

    

    def __enter__(self):

        """Context manager entry"""

        return self

    

    def __exit__(self, exc_type, exc_val, exc_tb):

        """Context manager exit"""

        self.close()

