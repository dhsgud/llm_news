"""
Signal Generation Module

This module contains classes for quantifying sentiment, fetching VIX data,
and calculating buy/sell signals based on sentiment analysis and market volatility.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import math
import logging

logger = logging.getLogger(__name__)


class SentimentQuantifier:
    """
    Quantifies sentiment analysis results into numerical scores.
    Applies conservative weighting to negative sentiment.
    """
    
    # Sentiment score constants
    POSITIVE_SCORE = 1.0
    NEUTRAL_SCORE = 0.0
    NEGATIVE_SCORE = -1.0
    NEGATIVE_WEIGHT = 1.5  # Conservative bias - negative news weighted more heavily
    
    def quantify(self, sentiment: str) -> float:
        """
        Convert sentiment string to numerical score.
        
        Args:
            sentiment: Sentiment classification ('Positive', 'Negative', 'Neutral')
            
        Returns:
            float: Quantified score (-1.5 for Negative, 0.0 for Neutral, 1.0 for Positive)
        """
        sentiment_upper = sentiment.upper()
        
        if sentiment_upper == 'POSITIVE':
            return self.POSITIVE_SCORE
        elif sentiment_upper == 'NEGATIVE':
            # Apply conservative weight to negative sentiment
            return self.NEGATIVE_SCORE * self.NEGATIVE_WEIGHT
        elif sentiment_upper == 'NEUTRAL':
            return self.NEUTRAL_SCORE
        else:
            logger.warning(f"Unknown sentiment value: {sentiment}, defaulting to NEUTRAL")
            return self.NEUTRAL_SCORE
    
    def calculate_daily_score(self, sentiment_results: List[Dict]) -> float:
        """
        Calculate aggregated sentiment score for a single day.
        
        Args:
            sentiment_results: List of sentiment analysis results for the day
                Each dict should have 'sentiment' key with value 'Positive', 'Negative', or 'Neutral'
                
        Returns:
            float: Average sentiment score for the day
        """
        if not sentiment_results:
            logger.warning("No sentiment results provided for daily score calculation")
            return self.NEUTRAL_SCORE
        
        total_score = 0.0
        for result in sentiment_results:
            sentiment = result.get('sentiment', 'Neutral')
            score = self.quantify(sentiment)
            total_score += score
        
        # Calculate average score
        daily_score = total_score / len(sentiment_results)
        
        logger.info(f"Calculated daily score: {daily_score:.2f} from {len(sentiment_results)} articles")
        return daily_score
    
    def calculate_weekly_scores(self, sentiment_data: List[Dict]) -> Dict[str, float]:
        """
        Calculate daily sentiment scores for a week.
        
        Args:
            sentiment_data: List of sentiment results with 'analyzed_at' or 'date' field
            
        Returns:
            Dict mapping date strings (YYYY-MM-DD) to daily scores
        """
        # Group sentiment results by date
        daily_groups = {}
        
        for result in sentiment_data:
            # Get date from result
            date_field = result.get('analyzed_at') or result.get('date')
            if not date_field:
                logger.warning("Sentiment result missing date field, skipping")
                continue
            
            # Convert to date string
            if isinstance(date_field, datetime):
                date_str = date_field.strftime('%Y-%m-%d')
            elif isinstance(date_field, str):
                # Assume ISO format or extract date part
                date_str = date_field.split('T')[0] if 'T' in date_field else date_field[:10]
            else:
                logger.warning(f"Unknown date format: {date_field}, skipping")
                continue
            
            if date_str not in daily_groups:
                daily_groups[date_str] = []
            daily_groups[date_str].append(result)
        
        # Calculate score for each day
        weekly_scores = {}
        for date_str, results in daily_groups.items():
            weekly_scores[date_str] = self.calculate_daily_score(results)
        
        logger.info(f"Calculated weekly scores for {len(weekly_scores)} days")
        return weekly_scores



class VIXFetcher:
    """
    Fetches VIX (Volatility Index) data from external APIs.
    Normalizes VIX values to 0-1 range for signal calculation.
    """
    
    # VIX typical range for normalization
    VIX_MIN = 10.0  # Historically low VIX
    VIX_MAX = 80.0  # Historically high VIX (extreme fear)
    VIX_NORMAL_MIN = 10.0
    VIX_NORMAL_MAX = 40.0  # More realistic upper bound for normal conditions
    
    def __init__(self, api_key: Optional[str] = None, api_source: str = "yahoo"):
        """
        Initialize VIX fetcher.
        
        Args:
            api_key: API key for the data source (if required)
            api_source: Data source ('yahoo', 'alphavantage', 'mock')
        """
        self.api_key = api_key
        self.api_source = api_source.lower()
        logger.info(f"VIXFetcher initialized with source: {self.api_source}")
    
    def get_current_vix(self) -> float:
        """
        Fetch current VIX value from the configured API source.
        
        Returns:
            float: Current VIX value
            
        Raises:
            Exception: If API call fails
        """
        if self.api_source == "mock":
            # Return mock VIX for testing
            mock_vix = 18.5
            logger.info(f"Using mock VIX value: {mock_vix}")
            return mock_vix
        
        elif self.api_source == "yahoo":
            return self._fetch_from_yahoo()
        
        elif self.api_source == "alphavantage":
            if not self.api_key:
                raise ValueError("API key required for Alpha Vantage")
            return self._fetch_from_alphavantage()
        
        else:
            raise ValueError(f"Unsupported API source: {self.api_source}")
    
    def _fetch_from_yahoo(self) -> float:
        """
        Fetch VIX from Yahoo Finance.
        
        Returns:
            float: Current VIX value
        """
        try:
            import requests
            
            # Yahoo Finance API endpoint for VIX (^VIX)
            url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX"
            params = {
                "interval": "1d",
                "range": "1d"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            vix_value = data['chart']['result'][0]['meta']['regularMarketPrice']
            
            logger.info(f"Fetched VIX from Yahoo Finance: {vix_value}")
            return float(vix_value)
            
        except Exception as e:
            logger.error(f"Failed to fetch VIX from Yahoo Finance: {e}")
            # Return default moderate VIX on error
            return 20.0
    
    def _fetch_from_alphavantage(self) -> float:
        """
        Fetch VIX from Alpha Vantage.
        
        Returns:
            float: Current VIX value
        """
        try:
            import requests
            
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": "VIX",
                "apikey": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            vix_value = data['Global Quote']['05. price']
            
            logger.info(f"Fetched VIX from Alpha Vantage: {vix_value}")
            return float(vix_value)
            
        except Exception as e:
            logger.error(f"Failed to fetch VIX from Alpha Vantage: {e}")
            # Return default moderate VIX on error
            return 20.0
    
    def normalize_vix(self, vix: float) -> float:
        """
        Normalize VIX value to 0-1 range.
        Uses realistic bounds (10-40) for better signal sensitivity.
        
        Args:
            vix: Raw VIX value
            
        Returns:
            float: Normalized VIX in range [0, 1]
        """
        # Clamp VIX to reasonable bounds
        clamped_vix = max(self.VIX_NORMAL_MIN, min(vix, self.VIX_NORMAL_MAX))
        
        # Normalize to 0-1 range
        normalized = (clamped_vix - self.VIX_NORMAL_MIN) / (self.VIX_NORMAL_MAX - self.VIX_NORMAL_MIN)
        
        logger.debug(f"Normalized VIX {vix:.2f} -> {normalized:.3f}")
        return normalized
    
    def get_normalized_vix(self) -> float:
        """
        Fetch and normalize VIX in one call.
        
        Returns:
            float: Normalized VIX value (0-1 range)
        """
        vix = self.get_current_vix()
        return self.normalize_vix(vix)



class SignalCalculator:
    """
    Calculates buy/sell signals based on sentiment scores and VIX.
    Implements conservative signal generation with VIX-weighted sentiment.
    """
    
    def __init__(self, quantifier: Optional[SentimentQuantifier] = None, 
                 vix_fetcher: Optional[VIXFetcher] = None):
        """
        Initialize signal calculator.
        
        Args:
            quantifier: SentimentQuantifier instance (creates new if None)
            vix_fetcher: VIXFetcher instance (creates new if None)
        """
        self.quantifier = quantifier or SentimentQuantifier()
        self.vix_fetcher = vix_fetcher or VIXFetcher(api_source="mock")
        logger.info("SignalCalculator initialized")
    
    def calculate_weekly_signal(self, daily_scores: List[float], 
                                vix_normalized: Optional[float] = None) -> float:
        """
        Calculate weekly signal score using VIX-weighted sentiment.
        
        Formula: Weekly_Signal = Σ(Daily_Score × (1 + VIX_Normalized))
        
        Args:
            daily_scores: List of daily sentiment scores
            vix_normalized: Normalized VIX value (0-1). If None, fetches current VIX.
            
        Returns:
            float: Raw weekly signal score
        """
        if not daily_scores:
            logger.warning("No daily scores provided for signal calculation")
            return 0.0
        
        # Get VIX if not provided
        if vix_normalized is None:
            vix_normalized = self.vix_fetcher.get_normalized_vix()
        
        # Calculate VIX weight (higher VIX = more weight on sentiment)
        vix_weight = 1.0 + vix_normalized
        
        # Calculate weighted sum
        weighted_sum = sum(score * vix_weight for score in daily_scores)
        
        logger.info(f"Weekly signal calculated: {weighted_sum:.2f} "
                   f"(VIX weight: {vix_weight:.2f}, days: {len(daily_scores)})")
        
        return weighted_sum
    
    def sigmoid(self, x: float, center: float = 0.0, steepness: float = 1.0) -> float:
        """
        Sigmoid normalization function.
        
        Args:
            x: Input value
            center: Center point of sigmoid (inflection point)
            steepness: Steepness of the curve (higher = steeper)
            
        Returns:
            float: Value in range [0, 1]
        """
        try:
            return 1.0 / (1.0 + math.exp(-steepness * (x - center)))
        except OverflowError:
            # Handle extreme values
            return 0.0 if x < center else 1.0
    
    def normalize_to_ratio(self, signal_score: float, method: str = "sigmoid") -> int:
        """
        Normalize signal score to 0-100 buy/sell ratio.
        
        - 0-30: Strong Sell (red)
        - 31-70: Neutral (yellow)
        - 71-100: Strong Buy (green)
        
        Args:
            signal_score: Raw signal score from calculate_weekly_signal
            method: Normalization method ('sigmoid' or 'linear')
            
        Returns:
            int: Buy/sell ratio in range [0, 100]
        """
        if method == "sigmoid":
            # Use sigmoid with center at 0 (neutral sentiment)
            # Steepness adjusted for typical signal range (-10 to +10)
            normalized = self.sigmoid(signal_score, center=0.0, steepness=0.3)
            ratio = int(normalized * 100)
            
        elif method == "linear":
            # Linear normalization with typical range
            # Assume signal range: -15 (very negative) to +10 (very positive)
            min_signal = -15.0
            max_signal = 10.0
            
            # Clamp to range
            clamped = max(min_signal, min(signal_score, max_signal))
            
            # Normalize to 0-1
            normalized = (clamped - min_signal) / (max_signal - min_signal)
            ratio = int(normalized * 100)
            
        else:
            raise ValueError(f"Unknown normalization method: {method}")
        
        # Ensure ratio is in valid range
        ratio = max(0, min(100, ratio))
        
        logger.info(f"Normalized signal {signal_score:.2f} to ratio {ratio} using {method}")
        return ratio
    
    def calculate_buy_sell_ratio(self, sentiment_data: List[Dict], 
                                 vix_normalized: Optional[float] = None,
                                 normalization_method: str = "sigmoid") -> Dict:
        """
        Complete pipeline: sentiment data -> buy/sell ratio.
        
        Args:
            sentiment_data: List of sentiment analysis results
            vix_normalized: Optional pre-fetched normalized VIX
            normalization_method: Method for ratio normalization
            
        Returns:
            Dict with keys:
                - ratio: int (0-100)
                - signal_score: float (raw score)
                - daily_scores: Dict[str, float]
                - vix_normalized: float
                - interpretation: str
        """
        # Calculate daily scores
        weekly_scores = self.quantifier.calculate_weekly_scores(sentiment_data)
        daily_scores_list = list(weekly_scores.values())
        
        if not daily_scores_list:
            logger.warning("No daily scores calculated, returning neutral signal")
            return {
                "ratio": 50,
                "signal_score": 0.0,
                "daily_scores": {},
                "vix_normalized": 0.0,
                "interpretation": "Neutral"
            }
        
        # Get VIX if not provided
        if vix_normalized is None:
            vix_normalized = self.vix_fetcher.get_normalized_vix()
        
        # Calculate weekly signal
        signal_score = self.calculate_weekly_signal(daily_scores_list, vix_normalized)
        
        # Normalize to ratio
        ratio = self.normalize_to_ratio(signal_score, method=normalization_method)
        
        # Interpret ratio
        if ratio <= 30:
            interpretation = "Strong Sell"
        elif ratio <= 70:
            interpretation = "Neutral"
        else:
            interpretation = "Strong Buy"
        
        result = {
            "ratio": ratio,
            "signal_score": signal_score,
            "daily_scores": weekly_scores,
            "vix_normalized": vix_normalized,
            "interpretation": interpretation
        }
        
        logger.info(f"Buy/Sell ratio calculated: {ratio} ({interpretation})")
        return result
