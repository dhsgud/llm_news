"""

Social Sentiment Analyzer

Analyzes sentiment of social media posts using LLM

"""



import logging

from datetime import datetime, timedelta

from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from sqlalchemy import func



try:

    from models.social_models import (

        SocialPost, SocialSentiment, SocialSentimentCreate,

        AggregatedSocialSentiment, SocialSentimentSummary

    )

    from services.llm_client import LlamaCppClient

except ImportError:

    from models.social_models import (

        SocialPost, SocialSentiment, SocialSentimentCreate,

        AggregatedSocialSentiment, SocialSentimentSummary

    )

    from services.llm_client import LlamaCppClient





logger = logging.getLogger(__name__)





class SocialSentimentAnalyzer:

    """Analyzes sentiment of social media posts"""

    

    def __init__(self, db: Session, llm_client: LlamaCppClient):

        self.db = db

        self.llm_client = llm_client

    

    def create_sentiment_prompt(self, post: SocialPost) -> str:

        """Create prompt for social post sentiment analysis"""

        prompt = f"""Analyze the sentiment of this {post.platform} post about stocks/finance.



Post: "{post.content}"

Author: {post.author}

Engagement: {post.likes} likes, {post.comments} comments



Classify the sentiment as Positive, Negative, or Neutral.

Provide a score from -1.5 (very negative) to 1.0 (very positive).

Also provide a confidence score from 0.0 to 1.0.



Consider:

- Bullish/bearish language

- Emojis and slang (??, _�, "
  "sentiment": "Positive|Negative|Neutral",

  "score": <float>,

  "confidence": <float>,

  "reasoning": "<brief explanation>"

}}"""

        return prompt

    

    def parse_sentiment_response(self, response: str) -> Optional[Dict]:

        """Parse LLM response for sentiment analysis"""

        try:

            import json

            # Extract JSON from response

            start = response.find('{')

            end = response.rfind('}') + 1

            if start >= 0 and end > start:

                json_str = response[start:end]

                result = json.loads(json_str)

                

                # Validate required fields

                if all(k in result for k in ['sentiment', 'score', 'confidence']):

                    return result

            

            logger.warning(f"Could not parse sentiment response: {response[:100]}")

            return None

            

        except Exception as e:

            logger.error(f"Error parsing sentiment response: {e}")

            return None

    

    def analyze_post(self, post: SocialPost) -> Optional[SocialSentimentCreate]:

        """Analyze sentiment of a single post"""

        # Check if already analyzed

        existing = self.db.query(SocialSentiment).filter(

            SocialSentiment.post_id == post.id

        ).first()

        

        if existing:

            logger.debug(f"Post {post.id} already analyzed")

            return None

        

        # Create prompt and get LLM response

        prompt = self.create_sentiment_prompt(post)

        response = self.llm_client.generate(prompt, max_tokens=200, temperature=0.3)

        

        if not response:

            logger.error(f"No response from LLM for post {post.id}")

            return None

        

        # Parse response

        result = self.parse_sentiment_response(response)

        if not result:

            return None

        

        # Create sentiment object

        sentiment = SocialSentimentCreate(

            post_id=post.id,

            sentiment=result['sentiment'],

            score=float(result['score']),

            confidence=float(result['confidence']),

            reasoning=result.get('reasoning', '')

        )

        

        return sentiment

    

    def analyze_batch(self, posts: List[SocialPost]) -> int:

        """Analyze sentiment for multiple posts"""

        analyzed_count = 0

        

        for post in posts:

            try:

                sentiment_data = self.analyze_post(post)

                if sentiment_data:

                    sentiment = SocialSentiment(**sentiment_data.model_dump())

                    self.db.add(sentiment)

                    analyzed_count += 1

                    

                    # Commit every 10 posts

                    if analyzed_count % 10 == 0:

                        self.db.commit()

                        logger.info(f"Analyzed {analyzed_count} posts so far")

                        

            except Exception as e:

                logger.error(f"Error analyzing post {post.id}: {e}")

                continue

        

        self.db.commit()

        logger.info(f"Completed analysis of {analyzed_count} posts")

        return analyzed_count

    

    def get_unanalyzed_posts(self, limit: int = 100) -> List[SocialPost]:

        """Get posts that haven't been analyzed yet"""

        # Subquery to get analyzed post IDs

        analyzed_ids = self.db.query(SocialSentiment.post_id).subquery()

        

        # Get posts not in analyzed list

        posts = self.db.query(SocialPost).filter(

            ~SocialPost.id.in_(analyzed_ids)

        ).order_by(SocialPost.created_at.desc()).limit(limit).all()

        

        return posts

    

    def aggregate_sentiment(self, symbol: Optional[str] = None, days: int = 7) -> Dict:

        """

        Aggregate sentiment data for a symbol or overall market

        

        Args:

            symbol: Stock symbol (None for overall market)

            days: Number of days to aggregate

        

        Returns:

            Dictionary with aggregated sentiment data

        """

        cutoff_date = datetime.now() - timedelta(days=days)

        

        # Build query

        query = self.db.query(

            SocialPost.platform,

            func.count(SocialPost.id).label('post_count'),

            func.avg(SocialSentiment.score).label('avg_score'),

            func.sum(SocialPost.likes + SocialPost.shares + SocialPost.comments).label('total_engagement'),

            func.sum(func.case((SocialSentiment.sentiment == 'Positive', 1), else_=0)).label('positive_count'),

            func.sum(func.case((SocialSentiment.sentiment == 'Negative', 1), else_=0)).label('negative_count'),

            func.sum(func.case((SocialSentiment.sentiment == 'Neutral', 1), else_=0)).label('neutral_count')

        ).join(SocialSentiment, SocialPost.id == SocialSentiment.post_id).filter(

            SocialPost.created_at >= cutoff_date

        )

        

        if symbol:

            query = query.filter(SocialPost.symbol == symbol)

        

        query = query.group_by(SocialPost.platform)

        

        results = query.all()

        

        # Format results

        aggregated = {}

        for row in results:

            aggregated[row.platform] = {

                'post_count': row.post_count,

                'avg_sentiment': float(row.avg_score) if row.avg_score else 0.0,

                'total_engagement': row.total_engagement or 0,

                'positive_count': row.positive_count or 0,

                'negative_count': row.negative_count or 0,

                'neutral_count': row.neutral_count or 0,

                'trending_score': self._calculate_trending_score(

                    row.avg_score or 0.0,

                    row.total_engagement or 0,

                    row.post_count or 1

                )

            }

        

        return aggregated

    

    def _calculate_trending_score(self, avg_sentiment: float, engagement: int, post_count: int) -> float:

        """

        Calculate trending score based on sentiment and engagement

        Higher engagement and stronger sentiment = higher trending score

        """

        # Normalize engagement (log scale)

        import math

        engagement_score = math.log10(max(engagement, 1))

        

        # Weight sentiment by engagement

        trending = (avg_sentiment * engagement_score) / max(post_count, 1)

        

        return round(trending, 3)

    

    def save_aggregated_sentiment(self, symbol: Optional[str] = None):

        """Save aggregated sentiment to database"""

        aggregated = self.aggregate_sentiment(symbol=symbol)

        

        for platform, data in aggregated.items():

            agg_sentiment = AggregatedSocialSentiment(

                symbol=symbol,

                date=datetime.now(),

                platform=platform,

                post_count=data['post_count'],

                avg_sentiment_score=data['avg_sentiment'],

                positive_count=data['positive_count'],

                negative_count=data['negative_count'],

                neutral_count=data['neutral_count'],

                total_engagement=data['total_engagement']

            )

            self.db.add(agg_sentiment)

        

        self.db.commit()

        logger.info(f"Saved aggregated sentiment for {symbol or 'market'}")

    

    def get_sentiment_summary(self, symbol: Optional[str] = None, days: int = 7) -> List[SocialSentimentSummary]:

        """Get sentiment summary for display"""

        aggregated = self.aggregate_sentiment(symbol=symbol, days=days)

        

        summaries = []

        for platform, data in aggregated.items():

            summary = SocialSentimentSummary(

                symbol=symbol,

                platform=platform,

                total_posts=data['post_count'],

                avg_sentiment=data['avg_sentiment'],

                sentiment_distribution={

                    'positive': data['positive_count'],

                    'negative': data['negative_count'],

                    'neutral': data['neutral_count']

                },

                total_engagement=data['total_engagement'],

                trending_score=data['trending_score']

            )

            summaries.append(summary)

        

        return summaries

