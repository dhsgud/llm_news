"""

Stock News Filter Module



Filters and associates news articles with specific stock symbols.

Performs stock-specific sentiment analysis.



Requirements: 11.4, 11.5

"""



import logging

import re

from typing import List, Dict, Optional, Set

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from sqlalchemy import and_, or_



from models.news_article import NewsArticle

from models.stock_news_relation import StockNewsRelation, StockNewsRelationCreate

from models.sentiment_analysis import SentimentAnalysis

from services.sentiment_analyzer import SentimentAnalyzer

from app.database import SessionLocal



logger = logging.getLogger(__name__)





# Korean stock name mappings (symbol -> company names)

STOCK_NAME_MAPPINGS = {

    "005930": ["Samsung Electronics", "Samsung"],
    "000660": ["SK Hynix", "Hynix"],
    "035420": ["NAVER", "Naver"],
    "035720": ["Kakao"],
    "051910": ["LG Chem", "LG"],
    "006400": ["Samsung SDI", "SDI"],

    "207940": ["Samsung Biologics"],
    "005380": ["Hyundai Motor", "Hyundai"],
    "000270": ["Kia"],
    "068270": ["Celltrion"],
    "028260": ["Samsung C&T"],
    "105560": ["KB Financial", "KB"],
    "055550": ["Shinhan Financial", "Shinhan"],
    "012330": ["Hyundai Mobis", "Mobis"],

    "017670": ["SK Telecom", "SKT"],
    "066570": ["LG Electronics", "LGE"],
    "003550": ["LG Corp", "LG"],
    "096770": ["SK Innovation"],
    "034730": ["SK Inc", "SK"],
    "009150": ["Samsung Electro-Mechanics", "SEMCO"]
}





class StockNewsFilter:

    """

    Filters news articles by stock symbols and performs stock-specific analysis

    

    Responsibilities:

    - Associate news articles with stock symbols

    - Calculate relevance scores

    - Perform stock-specific sentiment analysis

    

    Requirements: 11.4, 11.5

    """

    

    def __init__(

        self,

        sentiment_analyzer: Optional[SentimentAnalyzer] = None,

        stock_mappings: Optional[Dict[str, List[str]]] = None

    ):

        """

        Initialize stock news filter

        

        Args:

            sentiment_analyzer: SentimentAnalyzer instance for analysis

            stock_mappings: Custom stock symbol to name mappings

        """

        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()

        self.stock_mappings = stock_mappings or STOCK_NAME_MAPPINGS

        

        # Build reverse mapping (name -> symbol) for faster lookup

        self.name_to_symbol = {}

        for symbol, names in self.stock_mappings.items():

            for name in names:

                self.name_to_symbol[name.lower()] = symbol

        

        logger.info(

            f"StockNewsFilter initialized with {len(self.stock_mappings)} "

            f"stock mappings"

        )

    

    def filter_news_by_stock(

        self,

        symbol: str,

        days: int = 7,

        db: Session = None

    ) -> List[NewsArticle]:

        """

        Get news articles related to a specific stock

        

        Args:

            symbol: Stock symbol to filter by

            days: Number of days to look back

            db: Database session (optional)

            

        Returns:

            List of related NewsArticle objects

            

        Requirements: 11.4

        """

        should_close = False

        if db is None:

            db = SessionLocal()

            should_close = True

        

        try:

            cutoff_date = datetime.now() - timedelta(days=days)

            

            # Get existing relations

            relations = db.query(StockNewsRelation).filter(

                StockNewsRelation.stock_symbol == symbol

            ).all()

            

            article_ids = [r.article_id for r in relations]

            

            if not article_ids:

                logger.info(f"No news articles found for stock {symbol}")

                return []

            

            # Get articles

            articles = db.query(NewsArticle).filter(

                and_(

                    NewsArticle.id.in_(article_ids),

                    NewsArticle.published_date >= cutoff_date

                )

            ).order_by(NewsArticle.published_date.desc()).all()

            

            logger.info(

                f"Found {len(articles)} news articles for stock {symbol} "

                f"in last {days} days"

            )

            

            return articles

            

        except Exception as e:

            logger.error(f"Failed to filter news for stock {symbol}: {e}")

            return []

        finally:

            if should_close:

                db.close()

    

    def associate_news_with_stocks(

        self,

        article: NewsArticle,

        db: Session

    ) -> List[str]:

        """

        Associate a news article with relevant stock symbols

        

        Analyzes article content to identify mentioned stocks and creates

        relations with relevance scores.

        

        Args:

            article: NewsArticle to analyze

            db: Database session

            

        Returns:

            List of associated stock symbols

            

        Requirements: 11.4

        """

        try:

            # Find mentioned stocks in article

            mentioned_stocks = self._find_mentioned_stocks(article)

            

            if not mentioned_stocks:

                logger.debug(f"No stocks mentioned in article {article.id}")

                return []

            

            associated_symbols = []

            

            for symbol, relevance_score in mentioned_stocks.items():

                # Check if relation already exists

                existing = db.query(StockNewsRelation).filter(

                    and_(

                        StockNewsRelation.stock_symbol == symbol,

                        StockNewsRelation.article_id == article.id

                    )

                ).first()

                

                if existing:

                    logger.debug(

                        f"Relation already exists: article {article.id} - stock {symbol}"

                    )

                    continue

                

                # Create new relation

                relation = StockNewsRelation(

                    stock_symbol=symbol,

                    article_id=article.id,

                    relevance_score=relevance_score

                )

                

                db.add(relation)

                associated_symbols.append(symbol)

                

                logger.debug(

                    f"Associated article {article.id} with stock {symbol} "

                    f"(relevance: {relevance_score:.2f})"

                )

            

            db.commit()

            

            logger.info(

                f"Article {article.id} associated with {len(associated_symbols)} stocks"

            )

            

            return associated_symbols

            

        except Exception as e:

            logger.error(f"Failed to associate article {article.id} with stocks: {e}")

            db.rollback()

            return []

    

    def batch_associate_news(

        self,

        days: int = 7,

        db: Session = None

    ) -> Dict[str, int]:

        """

        Associate all recent news articles with stocks

        

        Args:

            days: Number of days to look back

            db: Database session (optional)

            

        Returns:

            Dict with statistics (articles_processed, relations_created)

        """

        should_close = False

        if db is None:

            db = SessionLocal()

            should_close = True

        

        try:

            cutoff_date = datetime.now() - timedelta(days=days)

            

            # Get recent articles

            articles = db.query(NewsArticle).filter(

                NewsArticle.published_date >= cutoff_date

            ).all()

            

            logger.info(f"Processing {len(articles)} articles for stock association")

            

            total_relations = 0

            

            for article in articles:

                symbols = self.associate_news_with_stocks(article, db)

                total_relations += len(symbols)

            

            stats = {

                "articles_processed": len(articles),

                "relations_created": total_relations

            }

            

            logger.info(

                f"Batch association completed: {stats['articles_processed']} articles, "

                f"{stats['relations_created']} relations created"

            )

            

            return stats

            

        except Exception as e:

            logger.error(f"Failed to batch associate news: {e}")

            return {"articles_processed": 0, "relations_created": 0}

        finally:

            if should_close:

                db.close()

    

    def get_stock_sentiment(

        self,

        symbol: str,

        days: int = 7,

        db: Session = None

    ) -> Dict:

        """

        Get aggregated sentiment analysis for a specific stock

        

        Args:

            symbol: Stock symbol

            days: Number of days to analyze

            db: Database session (optional)

            

        Returns:

            Dict with sentiment statistics and recent articles

            

        Requirements: 11.5

        """

        should_close = False

        if db is None:

            db = SessionLocal()

            should_close = True

        

        try:

            # Get related articles

            articles = self.filter_news_by_stock(symbol, days, db)

            

            if not articles:

                return {

                    "symbol": symbol,

                    "article_count": 0,

                    "average_score": 0.0,

                    "sentiment_distribution": {

                        "Positive": 0,

                        "Negative": 0,

                        "Neutral": 0

                    },

                    "recent_articles": []

                }

            

            # Get sentiment analyses for these articles

            article_ids = [a.id for a in articles]

            sentiments = db.query(SentimentAnalysis).filter(

                SentimentAnalysis.article_id.in_(article_ids)

            ).all()

            

            # Calculate statistics

            sentiment_distribution = {

                "Positive": 0,

                "Negative": 0,

                "Neutral": 0

            }

            

            total_score = 0.0

            

            for sentiment in sentiments:

                sentiment_distribution[sentiment.sentiment] += 1

                total_score += sentiment.score

            

            average_score = total_score / len(sentiments) if sentiments else 0.0

            

            # Get recent articles with sentiment

            recent_articles = []

            for article in articles[:10]:  # Limit to 10 most recent

                sentiment = next(

                    (s for s in sentiments if s.article_id == article.id),

                    None

                )

                

                recent_articles.append({

                    "id": article.id,

                    "title": article.title,

                    "published_date": article.published_date.isoformat(),

                    "sentiment": sentiment.sentiment if sentiment else None,

                    "score": float(sentiment.score) if sentiment else None,

                    "reasoning": sentiment.reasoning if sentiment else None

                })

            

            result = {

                "symbol": symbol,

                "article_count": len(articles),

                "sentiment_count": len(sentiments),

                "average_score": round(average_score, 2),

                "sentiment_distribution": sentiment_distribution,

                "recent_articles": recent_articles,

                "period_days": days

            }

            

            logger.info(

                f"Stock sentiment for {symbol}: {len(articles)} articles, "

                f"avg score: {average_score:.2f}"

            )

            

            return result

            

        except Exception as e:

            logger.error(f"Failed to get stock sentiment for {symbol}: {e}")

            return {

                "symbol": symbol,

                "error": str(e)

            }

        finally:

            if should_close:

                db.close()

    

    def analyze_stock_news(

        self,

        symbol: str,

        days: int = 7,

        db: Session = None

    ) -> int:

        """

        Analyze sentiment for all news related to a stock

        

        Args:

            symbol: Stock symbol

            days: Number of days to analyze

            db: Database session (optional)

            

        Returns:

            Number of articles analyzed

            

        Requirements: 11.5

        """

        should_close = False

        if db is None:

            db = SessionLocal()

            should_close = True

        

        try:

            # Get related articles

            articles = self.filter_news_by_stock(symbol, days, db)

            

            if not articles:

                logger.info(f"No articles to analyze for stock {symbol}")

                return 0

            

            # Analyze articles that don't have sentiment yet

            analyzed_count = 0

            

            for article in articles:

                # Check if already analyzed

                existing = db.query(SentimentAnalysis).filter(

                    SentimentAnalysis.article_id == article.id

                ).first()

                

                if existing:

                    continue

                

                try:

                    # Analyze sentiment

                    result = self.sentiment_analyzer.analyze_article(article)

                    

                    # Save to database

                    sentiment = SentimentAnalysis(

                        article_id=result.article_id,

                        sentiment=result.sentiment,

                        score=result.score,

                        reasoning=result.reasoning

                    )

                    

                    db.add(sentiment)

                    analyzed_count += 1

                    

                except Exception as e:

                    logger.error(f"Failed to analyze article {article.id}: {e}")

                    continue

            

            db.commit()

            

            logger.info(

                f"Analyzed {analyzed_count} articles for stock {symbol}"

            )

            

            return analyzed_count

            

        except Exception as e:

            logger.error(f"Failed to analyze stock news for {symbol}: {e}")

            db.rollback()

            return 0

        finally:

            if should_close:

                db.close()

    

    def _find_mentioned_stocks(self, article: NewsArticle) -> Dict[str, float]:

        """

        Find stock symbols mentioned in article

        

        Args:

            article: NewsArticle to analyze

            

        Returns:

            Dict mapping stock symbols to relevance scores (0.0-1.0)

        """

        mentioned_stocks = {}

        

        # Combine title and content for analysis

        text = f"{article.title} {article.content}".lower()

        

        # Search for each stock name

        for name, symbol in self.name_to_symbol.items():

            # Count mentions

            mentions = len(re.findall(r'\b' + re.escape(name) + r'\b', text, re.IGNORECASE))

            

            if mentions > 0:

                # Calculate relevance score based on:

                # 1. Number of mentions

                # 2. Whether it's in the title (higher weight)

                title_mentions = len(

                    re.findall(r'\b' + re.escape(name) + r'\b', article.title.lower(), re.IGNORECASE)

                )

                

                # Base score from mentions (capped at 0.5)

                mention_score = min(mentions * 0.1, 0.5)

                

                # Title bonus (0.3)

                title_score = 0.3 if title_mentions > 0 else 0.0

                

                # Asset type bonus (0.2 if stock-related)

                asset_score = 0.2 if article.asset_type in ["stock", "general"] else 0.0

                

                relevance_score = min(mention_score + title_score + asset_score, 1.0)

                

                # Update if this symbol already exists (keep higher score)

                if symbol in mentioned_stocks:

                    mentioned_stocks[symbol] = max(mentioned_stocks[symbol], relevance_score)

                else:

                    mentioned_stocks[symbol] = relevance_score

        

        return mentioned_stocks

    

    def add_stock_mapping(self, symbol: str, names: List[str]) -> None:

        """

        Add a new stock symbol mapping

        

        Args:

            symbol: Stock symbol

            names: List of company names to associate

        """

        self.stock_mappings[symbol] = names

        

        # Update reverse mapping

        for name in names:

            self.name_to_symbol[name.lower()] = symbol

        

        logger.info(f"Added stock mapping: {symbol} -> {names}")

    

    def get_all_tracked_symbols(self) -> List[str]:

        """

        Get list of all tracked stock symbols

        

        Returns:

            List of stock symbols

        """

        return list(self.stock_mappings.keys())

