"""

News Fetcher Module

Handles news collection from external APIs and scheduling

"""



import logging

from datetime import datetime, timedelta

from typing import List, Optional, Dict, Any

from dataclasses import dataclass



import requests

from requests.adapters import HTTPAdapter

from urllib3.util.retry import Retry



try:

    from config import settings

    from models.news_article import NewsArticleCreate

except ImportError:

    from config import settings

    from models.news_article import NewsArticleCreate





logger = logging.getLogger(__name__)





@dataclass

class NewsAPIArticle:

    """Raw article data from News API"""

    title: str

    description: Optional[str]

    content: Optional[str]

    published_at: str

    source_name: str

    url: str





class NewsAPIClientError(Exception):

    """Base exception for News API client errors"""

    pass





class NewsAPIClient:

    """

    Client for fetching financial news from News API

    

    Handles:

    - News API authentication

    - Financial news filtering

    - Date range queries

    - Error handling and retries

    """

    

    # Financial keywords for filtering

    FINANCIAL_KEYWORDS = [

        "stock", "market", "trading", "investment", "finance",

        "economy", "cryptocurrency", "bitcoin", "ethereum",

        "nasdaq", "dow jones", "s&p 500", "forex", "bond",

        "금융", "주식", "?�장", "?�자", "경제", "코인", "비트코인"

    ]

    

    # News sources focused on finance

    FINANCIAL_SOURCES = [

        "bloomberg", "reuters", "financial-times", "wall-street-journal",

        "cnbc", "marketwatch", "business-insider", "the-economist"

    ]

    

    def __init__(

        self,

        api_key: Optional[str] = None,

        base_url: Optional[str] = None,

        timeout: int = 30,

        max_retries: int = 3

    ):

        """

        Initialize News API client

        

        Args:

            api_key: News API key (default from settings)

            base_url: Base URL for News API (default from settings)

            timeout: Request timeout in seconds

            max_retries: Maximum number of retry attempts

        """

        self.api_key = api_key or settings.news_api_key

        self.base_url = base_url or settings.news_api_base_url

        self.timeout = timeout

        

        if not self.api_key:

            logger.warning("News API key not configured. Set NEWS_API_KEY environment variable.")

        

        # Configure session with retry strategy

        self.session = self._create_session(max_retries)

        

        logger.info(f"Initialized NewsAPIClient: base_url={self.base_url}")

    

    def _create_session(self, max_retries: int) -> requests.Session:

        """

        Create requests session with retry configuration

        

        Args:

            max_retries: Maximum number of retries

            

        Returns:

            Configured requests.Session

        """

        session = requests.Session()

        

        retry_strategy = Retry(

            total=max_retries,

            backoff_factor=1,

            status_forcelist=[429, 500, 502, 503, 504],

            allowed_methods=["GET"],

            raise_on_status=False

        )

        

        adapter = HTTPAdapter(max_retries=retry_strategy)

        session.mount("http://", adapter)

        session.mount("https://", adapter)

        

        return session

    

    def fetch_news(

        self,

        query: str = "finance OR stock OR market OR cryptocurrency",

        from_date: Optional[datetime] = None,

        to_date: Optional[datetime] = None,

        language: str = "en",

        sort_by: str = "publishedAt",

        page_size: int = 100

    ) -> List[NewsArticleCreate]:

        """

        Fetch news articles from News API

        

        Args:

            query: Search query string

            from_date: Start date for news (default: 7 days ago)

            to_date: End date for news (default: now)

            language: Language code (en, ko, etc.)

            sort_by: Sort order (publishedAt, relevancy, popularity)

            page_size: Number of articles per page (max 100)

            

        Returns:

            List of NewsArticleCreate objects

            

        Raises:

            NewsAPIClientError: If API request fails

        """

        if not self.api_key:

            raise NewsAPIClientError("News API key not configured")

        

        # Set default date range (last 7 days)

        if from_date is None:

            from_date = datetime.now() - timedelta(days=7)

        if to_date is None:

            to_date = datetime.now()

        

        logger.info(

            f"Fetching news: query='{query}', from={from_date.date()}, "

            f"to={to_date.date()}, language={language}"

        )

        

        try:

            # Fetch articles from API

            raw_articles = self._fetch_everything(

                query=query,

                from_date=from_date,

                to_date=to_date,

                language=language,

                sort_by=sort_by,

                page_size=page_size

            )

            

            # Convert to NewsArticleCreate objects

            articles = self._convert_to_articles(raw_articles)

            

            # Filter for financial relevance

            filtered_articles = self.filter_financial_news(articles)

            

            logger.info(

                f"Fetched {len(raw_articles)} articles, "

                f"filtered to {len(filtered_articles)} financial articles"

            )

            

            return filtered_articles

            

        except Exception as e:

            logger.error(f"Failed to fetch news: {e}", exc_info=True)

            raise NewsAPIClientError(f"News fetch failed: {str(e)}") from e

    

    def _fetch_everything(

        self,

        query: str,

        from_date: datetime,

        to_date: datetime,

        language: str,

        sort_by: str,

        page_size: int

    ) -> List[Dict[str, Any]]:

        """

        Fetch articles from News API /everything endpoint

        

        Args:

            query: Search query

            from_date: Start date

            to_date: End date

            language: Language code

            sort_by: Sort order

            page_size: Results per page

            

        Returns:

            List of raw article dictionaries

            

        Raises:

            NewsAPIClientError: If request fails

        """

        url = f"{self.base_url}/everything"

        

        params = {

            "q": query,

            "from": from_date.strftime("%Y-%m-%d"),

            "to": to_date.strftime("%Y-%m-%d"),

            "language": language,

            "sortBy": sort_by,

            "pageSize": page_size,

            "apiKey": self.api_key

        }

        

        try:

            response = self.session.get(url, params=params, timeout=self.timeout)

            

            if response.status_code == 401:

                raise NewsAPIClientError("Invalid News API key")

            elif response.status_code == 429:

                raise NewsAPIClientError("News API rate limit exceeded")

            elif response.status_code != 200:

                raise NewsAPIClientError(

                    f"News API returned status {response.status_code}: {response.text}"

                )

            

            data = response.json()

            

            if data.get("status") != "ok":

                error_msg = data.get("message", "Unknown error")

                raise NewsAPIClientError(f"News API error: {error_msg}")

            

            articles = data.get("articles", [])

            total_results = data.get("totalResults", 0)

            

            logger.debug(f"News API returned {len(articles)} articles (total: {total_results})")

            

            return articles

            

        except requests.exceptions.Timeout:

            raise NewsAPIClientError(f"News API request timed out after {self.timeout}s")

        except requests.exceptions.ConnectionError as e:

            raise NewsAPIClientError(f"Failed to connect to News API: {e}")

        except requests.exceptions.RequestException as e:

            raise NewsAPIClientError(f"News API request failed: {e}")

    

    def _convert_to_articles(self, raw_articles: List[Dict[str, Any]]) -> List[NewsArticleCreate]:

        """

        Convert raw API response to NewsArticleCreate objects

        

        Args:

            raw_articles: List of raw article dictionaries from API

            

        Returns:

            List of NewsArticleCreate objects

        """

        articles = []

        

        for raw in raw_articles:

            try:

                # Extract fields from API response

                title = raw.get("title", "")

                description = raw.get("description", "")

                content = raw.get("content", "")

                

                # Combine description and content for full text

                full_content = f"{description}\n\n{content}" if description and content else (content or description or "")

                

                # Skip articles with no content

                if not title or not full_content:

                    continue

                

                # Parse published date

                published_at = raw.get("publishedAt", "")

                try:

                    published_date = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

                except (ValueError, AttributeError):

                    logger.warning(f"Invalid date format: {published_at}, using current time")

                    published_date = datetime.now()

                

                # Extract source name

                source = raw.get("source", {})

                source_name = source.get("name", "Unknown") if isinstance(source, dict) else "Unknown"

                

                # Get URL

                url = raw.get("url", "")

                

                # Get author
                author = raw.get("author", None)
                
                article = NewsArticleCreate(

                    title=title[:500],  # Truncate to max length

                    content=full_content,
                    
                    description=description[:1000] if description else None,
                    
                    author=author[:200] if author else None,

                    published_date=published_date,

                    source=source_name[:100],

                    url=url[:500] if url else None,

                    asset_type="general"

                )

                

                articles.append(article)

                

            except Exception as e:

                logger.warning(f"Failed to parse article: {e}")

                continue

        

        return articles

    

    def filter_financial_news(self, articles: List[NewsArticleCreate]) -> List[NewsArticleCreate]:

        """

        Filter articles for financial relevance

        

        Checks title and content for financial keywords

        

        Args:

            articles: List of NewsArticleCreate objects

            

        Returns:

            Filtered list of financial articles

        """

        filtered = []

        

        for article in articles:

            # Combine title and content for keyword search

            text = f"{article.title} {article.content}".lower()

            

            # Check if any financial keyword is present

            is_financial = any(keyword.lower() in text for keyword in self.FINANCIAL_KEYWORDS)

            

            if is_financial:

                filtered.append(article)

        

        return filtered

    

    def close(self):

        """Close the HTTP session"""

        self.session.close()

        logger.debug("NewsAPIClient session closed")

    

    def __enter__(self):

        """Context manager entry"""

        return self

    

    def __exit__(self, exc_type, exc_val, exc_tb):

        """Context manager exit"""

        self.close()







class NewsScheduler:

    """

    Scheduler for automated news collection

    

    Handles:

    - Daily news collection at scheduled time

    - Automatic cleanup of old news (>7 days)

    - Background task management

    """

    

    def __init__(

        self,

        db_session_factory,

        news_client: Optional[NewsAPIClient] = None,

        collection_hour: Optional[int] = None,

        collection_minute: Optional[int] = None,

        retention_days: Optional[int] = None

    ):

        """

        Initialize news scheduler

        

        Args:

            db_session_factory: Factory function to create database sessions

            news_client: NewsAPIClient instance (creates new if None)

            collection_hour: Hour to run collection (0-23, default from settings)

            collection_minute: Minute to run collection (0-59, default from settings)

            retention_days: Days to retain news (default from settings)

        """

        from apscheduler.schedulers.background import BackgroundScheduler

        from apscheduler.triggers.cron import CronTrigger

        

        self.db_session_factory = db_session_factory

        self.news_client = news_client or NewsAPIClient()

        self.collection_hour = collection_hour if collection_hour is not None else settings.news_collection_hour

        self.collection_minute = collection_minute if collection_minute is not None else settings.news_collection_minute

        self.retention_days = retention_days if retention_days is not None else settings.news_retention_days

        

        self.scheduler = BackgroundScheduler()

        self._is_running = False

        

        logger.info(

            f"Initialized NewsScheduler: collection_time={self.collection_hour:02d}:{self.collection_minute:02d}, "

            f"retention_days={self.retention_days}"

        )

    

    def schedule_daily_collection(self):

        """

        Schedule daily news collection task

        

        Sets up cron job to run at specified time each day

        """

        from apscheduler.triggers.cron import CronTrigger

        

        # Create cron trigger for daily execution

        trigger = CronTrigger(

            hour=self.collection_hour,

            minute=self.collection_minute

        )

        

        # Add job to scheduler

        self.scheduler.add_job(

            func=self.collect_and_store,

            trigger=trigger,

            id="daily_news_collection",

            name="Daily News Collection",

            replace_existing=True,

            max_instances=1  # Prevent overlapping executions

        )

        

        logger.info(

            f"Scheduled daily news collection at {self.collection_hour:02d}:{self.collection_minute:02d}"

        )

    

    def start(self):

        """

        Start the scheduler

        

        Begins background task execution

        """

        if not self._is_running:

            self.scheduler.start()

            self._is_running = True

            logger.info("NewsScheduler started")

        else:

            logger.warning("NewsScheduler is already running")

    

    def stop(self):

        """

        Stop the scheduler

        

        Shuts down background tasks gracefully

        """

        if self._is_running:

            self.scheduler.shutdown(wait=True)

            self._is_running = False

            logger.info("NewsScheduler stopped")

        else:

            logger.warning("NewsScheduler is not running")

    

    def collect_and_store(self):

        """

        Collect news from API and store in database

        

        This is the main task executed by the scheduler:

        1. Fetch news from API

        2. Store in database

        3. Clean up old news

        

        Handles errors gracefully to prevent scheduler from stopping

        """

        logger.info("Starting scheduled news collection")

        

        try:

            # Create database session

            db = self.db_session_factory()

            

            try:

                # Fetch news from last 7 days

                from_date = datetime.now() - timedelta(days=7)

                to_date = datetime.now()

                

                articles = self.news_client.fetch_news(

                    from_date=from_date,

                    to_date=to_date

                )

                

                if not articles:

                    logger.warning("No articles fetched from News API")

                    return

                

                # Store articles in database

                stored_count = self._store_articles(db, articles)

                

                logger.info(f"Stored {stored_count} new articles in database")

                

                # Clean up old news

                deleted_count = self.cleanup_old_news(db, days=self.retention_days)

                

                logger.info(f"Deleted {deleted_count} old articles (>{self.retention_days} days)")

                

                logger.info("Scheduled news collection completed successfully")

                

            finally:

                db.close()

                

        except NewsAPIClientError as e:

            logger.error(f"News API error during scheduled collection: {e}")

            # Don't raise - let scheduler continue

            

        except Exception as e:

            logger.error(f"Unexpected error during scheduled collection: {e}", exc_info=True)

            # Don't raise - let scheduler continue

    

    def _store_articles(self, db, articles: List[NewsArticleCreate]) -> int:

        """

        Store articles in database, avoiding duplicates

        

        Args:

            db: Database session

            articles: List of NewsArticleCreate objects

            

        Returns:

            Number of articles stored

        """

        from models.news_article import NewsArticle

        

        stored_count = 0

        

        for article_data in articles:

            try:

                # Check if article already exists (by URL or title+date)

                existing = None

                

                if article_data.url:

                    existing = db.query(NewsArticle).filter(

                        NewsArticle.url == article_data.url

                    ).first()

                

                if not existing:

                    # Also check by title and published date to catch duplicates without URLs

                    existing = db.query(NewsArticle).filter(

                        NewsArticle.title == article_data.title,

                        NewsArticle.published_date == article_data.published_date

                    ).first()

                

                if existing:

                    logger.debug(f"Article already exists: {article_data.title[:50]}...")

                    continue

                

                # Create new article

                article = NewsArticle(

                    title=article_data.title,

                    content=article_data.content,
                    
                    description=article_data.description,
                    
                    author=article_data.author,

                    published_date=article_data.published_date,

                    source=article_data.source,

                    url=article_data.url,

                    asset_type=article_data.asset_type

                )

                

                db.add(article)

                stored_count += 1

                

            except Exception as e:

                logger.error(f"Failed to store article: {e}")

                continue

        

        # Commit all articles at once

        try:

            db.commit()

        except Exception as e:

            logger.error(f"Failed to commit articles to database: {e}")

            db.rollback()

            raise

        

        return stored_count

    

    def cleanup_old_news(self, db, days: int = 7) -> int:

        """

        Delete news articles older than specified days

        

        Args:

            db: Database session

            days: Number of days to retain (default: 7)

            

        Returns:

            Number of articles deleted

        """

        from models.news_article import NewsArticle

        

        try:

            cutoff_date = datetime.now() - timedelta(days=days)

            

            # Delete old articles

            deleted = db.query(NewsArticle).filter(

                NewsArticle.published_date < cutoff_date

            ).delete()

            

            db.commit()

            

            logger.debug(f"Deleted {deleted} articles older than {cutoff_date.date()}")

            

            return deleted

            

        except Exception as e:

            logger.error(f"Failed to cleanup old news: {e}")

            db.rollback()

            return 0

    

    def run_now(self):

        """

        Run news collection immediately (for testing/manual trigger)

        

        Executes the collection task outside of the schedule

        """

        logger.info("Running news collection manually")

        self.collect_and_store()

    

    @property

    def is_running(self) -> bool:

        """Check if scheduler is running"""

        return self._is_running

    

    def get_next_run_time(self) -> Optional[datetime]:

        """

        Get the next scheduled run time

        

        Returns:

            Next run datetime or None if not scheduled

        """

        job = self.scheduler.get_job("daily_news_collection")

        if job:

            return job.next_run_time

        return None

