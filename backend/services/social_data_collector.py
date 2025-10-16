"""
Social Media Data Collector
Collects posts from Twitter and Reddit
"""

import os
import re
import logging
from datetime import datetime, timedelta
from typing import List, Optional
import requests
from sqlalchemy.orm import Session

try:
    from models.social_models import SocialPost, SocialPostCreate
    from config import settings
except ImportError:
    from models.social_models import SocialPost, SocialPostCreate
    from config import settings


logger = logging.getLogger(__name__)


class SocialDataCollector:
    """Collects social media posts from Twitter and Reddit"""
    
    def __init__(self, db: Session):
        self.db = db
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "MarketAnalyzer/1.0")
        
    def extract_stock_symbols(self, text: str) -> List[str]:
        """Extract stock symbols from text (e.g., $AAPL, $TSLA)"""
        pattern = r'\$([A-Z]{1,5})\b'
        symbols = re.findall(pattern, text)
        return list(set(symbols))  # Remove duplicates
    
    def collect_twitter_posts(self, query: str = "$", max_results: int = 100) -> List[SocialPostCreate]:
        """
        Collect tweets mentioning stock symbols
        Uses Twitter API v2
        """
        if not self.twitter_bearer_token:
            logger.warning("Twitter Bearer Token not configured")
            return []
        
        url = "https://api.twitter.com/2/tweets/search/recent"
        headers = {"Authorization": f"Bearer {self.twitter_bearer_token}"}
        
        # Search for tweets with stock symbols in the last 24 hours
        params = {
            "query": f"{query} -is:retweet lang:en",
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id",
            "user.fields": "username"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            posts = []
            users = {user['id']: user['username'] for user in data.get('includes', {}).get('users', [])}
            
            for tweet in data.get('data', []):
                symbols = self.extract_stock_symbols(tweet['text'])
                metrics = tweet.get('public_metrics', {})
                
                post = SocialPostCreate(
                    platform="twitter",
                    post_id=tweet['id'],
                    symbol=symbols[0] if symbols else None,
                    author=users.get(tweet.get('author_id'), 'unknown'),
                    content=tweet['text'],
                    url=f"https://twitter.com/i/web/status/{tweet['id']}",
                    likes=metrics.get('like_count', 0),
                    shares=metrics.get('retweet_count', 0),
                    comments=metrics.get('reply_count', 0),
                    created_at=datetime.fromisoformat(tweet['created_at'].replace('Z', '+00:00'))
                )
                posts.append(post)
            
            logger.info(f"Collected {len(posts)} tweets")
            return posts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error collecting Twitter data: {e}")
            return []
    
    def collect_reddit_posts(self, subreddit: str = "wallstreetbets", limit: int = 100) -> List[SocialPostCreate]:
        """
        Collect posts from Reddit
        Uses Reddit API
        """
        if not self.reddit_client_id or not self.reddit_client_secret:
            logger.warning("Reddit API credentials not configured")
            return []
        
        # Get OAuth token
        auth = requests.auth.HTTPBasicAuth(self.reddit_client_id, self.reddit_client_secret)
        data = {
            'grant_type': 'client_credentials'
        }
        headers = {'User-Agent': self.reddit_user_agent}
        
        try:
            # Get access token
            token_response = requests.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth,
                data=data,
                headers=headers,
                timeout=10
            )
            token_response.raise_for_status()
            token = token_response.json()['access_token']
            
            # Get posts
            headers['Authorization'] = f'bearer {token}'
            url = f'https://oauth.reddit.com/r/{subreddit}/hot'
            params = {'limit': limit}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            posts = []
            for post_data in data['data']['children']:
                post = post_data['data']
                text = f"{post.get('title', '')} {post.get('selftext', '')}"
                symbols = self.extract_stock_symbols(text)
                
                post_obj = SocialPostCreate(
                    platform="reddit",
                    post_id=post['id'],
                    symbol=symbols[0] if symbols else None,
                    author=post.get('author', 'unknown'),
                    content=text[:1000],  # Limit content length
                    url=f"https://reddit.com{post.get('permalink', '')}",
                    likes=post.get('ups', 0),
                    shares=0,  # Reddit doesn't have shares
                    comments=post.get('num_comments', 0),
                    created_at=datetime.fromtimestamp(post['created_utc'])
                )
                posts.append(post_obj)
            
            logger.info(f"Collected {len(posts)} Reddit posts from r/{subreddit}")
            return posts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error collecting Reddit data: {e}")
            return []
    
    def save_posts(self, posts: List[SocialPostCreate]) -> int:
        """Save posts to database, skip duplicates"""
        saved_count = 0
        
        for post_data in posts:
            # Check if post already exists
            existing = self.db.query(SocialPost).filter(
                SocialPost.post_id == post_data.post_id
            ).first()
            
            if not existing:
                post = SocialPost(**post_data.model_dump())
                self.db.add(post)
                saved_count += 1
        
        self.db.commit()
        logger.info(f"Saved {saved_count} new posts to database")
        return saved_count
    
    def collect_all(self, symbols: Optional[List[str]] = None) -> dict:
        """
        Collect posts from all platforms
        
        Args:
            symbols: Optional list of stock symbols to search for
        
        Returns:
            Dictionary with collection statistics
        """
        stats = {
            'twitter': 0,
            'reddit': 0,
            'total': 0
        }
        
        # Collect Twitter posts
        if symbols:
            for symbol in symbols:
                twitter_posts = self.collect_twitter_posts(query=f"${symbol}")
                stats['twitter'] += self.save_posts(twitter_posts)
        else:
            twitter_posts = self.collect_twitter_posts()
            stats['twitter'] += self.save_posts(twitter_posts)
        
        # Collect Reddit posts
        reddit_posts = self.collect_reddit_posts(subreddit="wallstreetbets")
        stats['reddit'] += self.save_posts(reddit_posts)
        
        # Also check stocks subreddit
        reddit_posts2 = self.collect_reddit_posts(subreddit="stocks")
        stats['reddit'] += self.save_posts(reddit_posts2)
        
        stats['total'] = stats['twitter'] + stats['reddit']
        
        logger.info(f"Collection complete: {stats}")
        return stats
    
    def cleanup_old_posts(self, days: int = 7):
        """Delete posts older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted = self.db.query(SocialPost).filter(
            SocialPost.created_at < cutoff_date
        ).delete()
        self.db.commit()
        logger.info(f"Deleted {deleted} old social posts")
        return deleted
