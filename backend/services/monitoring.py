"""
Monitoring and Metrics Collection Service
Tracks API performance, LLM inference times, and trading success rates
"""

import time
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from threading import Lock
import json

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and aggregates application metrics
    """
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize metrics collector
        
        Args:
            window_size: Number of recent metrics to keep in memory
        """
        self.window_size = window_size
        self._lock = Lock()
        
        # API metrics
        self.api_response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.api_request_counts: Dict[str, int] = defaultdict(int)
        self.api_error_counts: Dict[str, int] = defaultdict(int)
        
        # LLM metrics
        self.llm_inference_times: deque = deque(maxlen=window_size)
        self.llm_request_counts: int = 0
        self.llm_error_counts: int = 0
        self.llm_token_counts: deque = deque(maxlen=window_size)
        
        # Trading metrics
        self.trade_success_count: int = 0
        self.trade_failure_count: int = 0
        self.trade_amounts: deque = deque(maxlen=window_size)
        self.trade_profits: deque = deque(maxlen=window_size)
        
        # System metrics
        self.start_time = datetime.now()
        self.last_reset_time = datetime.now()
    
    def record_api_request(self, endpoint: str, response_time: float, success: bool = True):
        """
        Record API request metrics
        
        Args:
            endpoint: API endpoint path
            response_time: Response time in seconds
            success: Whether request was successful
        """
        with self._lock:
            self.api_response_times[endpoint].append(response_time)
            self.api_request_counts[endpoint] += 1
            
            if not success:
                self.api_error_counts[endpoint] += 1
            
            logger.debug(f"API metric recorded: {endpoint} - {response_time:.3f}s - {'success' if success else 'error'}")
    
    def record_llm_inference(self, inference_time: float, token_count: Optional[int] = None, success: bool = True):
        """
        Record LLM inference metrics
        
        Args:
            inference_time: Inference time in seconds
            token_count: Number of tokens generated
            success: Whether inference was successful
        """
        with self._lock:
            self.llm_inference_times.append(inference_time)
            self.llm_request_counts += 1
            
            if token_count:
                self.llm_token_counts.append(token_count)
            
            if not success:
                self.llm_error_counts += 1
            
            logger.debug(f"LLM metric recorded: {inference_time:.3f}s - {token_count or 0} tokens - {'success' if success else 'error'}")
    
    def record_trade(self, amount: float, profit: Optional[float] = None, success: bool = True):
        """
        Record trading metrics
        
        Args:
            amount: Trade amount
            profit: Profit/loss amount (if completed)
            success: Whether trade was successful
        """
        with self._lock:
            self.trade_amounts.append(amount)
            
            if profit is not None:
                self.trade_profits.append(profit)
            
            if success:
                self.trade_success_count += 1
            else:
                self.trade_failure_count += 1
            
            logger.debug(f"Trade metric recorded: {amount} - profit: {profit} - {'success' if success else 'failure'}")
    
    def get_api_metrics(self, endpoint: Optional[str] = None) -> Dict:
        """
        Get API metrics summary
        
        Args:
            endpoint: Specific endpoint to get metrics for (None for all)
        
        Returns:
            Dictionary containing API metrics
        """
        with self._lock:
            if endpoint:
                response_times = list(self.api_response_times.get(endpoint, []))
                return {
                    "endpoint": endpoint,
                    "request_count": self.api_request_counts.get(endpoint, 0),
                    "error_count": self.api_error_counts.get(endpoint, 0),
                    "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                    "min_response_time": min(response_times) if response_times else 0,
                    "max_response_time": max(response_times) if response_times else 0,
                    "p95_response_time": self._percentile(response_times, 95) if response_times else 0,
                    "p99_response_time": self._percentile(response_times, 99) if response_times else 0,
                }
            else:
                # Aggregate metrics for all endpoints
                all_metrics = {}
                for ep in list(self.api_response_times.keys()):
                    response_times = list(self.api_response_times.get(ep, []))
                    all_metrics[ep] = {
                        "endpoint": ep,
                        "request_count": self.api_request_counts.get(ep, 0),
                        "error_count": self.api_error_counts.get(ep, 0),
                        "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
                        "min_response_time": min(response_times) if response_times else 0,
                        "max_response_time": max(response_times) if response_times else 0,
                        "p95_response_time": self._percentile(response_times, 95) if response_times else 0,
                        "p99_response_time": self._percentile(response_times, 99) if response_times else 0,
                    }
                
                return {
                    "endpoints": all_metrics,
                    "total_requests": sum(self.api_request_counts.values()),
                    "total_errors": sum(self.api_error_counts.values()),
                }
    
    def get_llm_metrics(self) -> Dict:
        """
        Get LLM metrics summary
        
        Returns:
            Dictionary containing LLM metrics
        """
        with self._lock:
            inference_times = list(self.llm_inference_times)
            token_counts = list(self.llm_token_counts)
            
            return {
                "request_count": self.llm_request_counts,
                "error_count": self.llm_error_counts,
                "success_rate": (self.llm_request_counts - self.llm_error_counts) / self.llm_request_counts if self.llm_request_counts > 0 else 0,
                "avg_inference_time": sum(inference_times) / len(inference_times) if inference_times else 0,
                "min_inference_time": min(inference_times) if inference_times else 0,
                "max_inference_time": max(inference_times) if inference_times else 0,
                "p95_inference_time": self._percentile(inference_times, 95) if inference_times else 0,
                "p99_inference_time": self._percentile(inference_times, 99) if inference_times else 0,
                "avg_tokens": sum(token_counts) / len(token_counts) if token_counts else 0,
                "total_tokens": sum(token_counts),
            }
    
    def get_trading_metrics(self) -> Dict:
        """
        Get trading metrics summary
        
        Returns:
            Dictionary containing trading metrics
        """
        with self._lock:
            trade_amounts = list(self.trade_amounts)
            trade_profits = list(self.trade_profits)
            
            total_trades = self.trade_success_count + self.trade_failure_count
            
            return {
                "total_trades": total_trades,
                "success_count": self.trade_success_count,
                "failure_count": self.trade_failure_count,
                "success_rate": self.trade_success_count / total_trades if total_trades > 0 else 0,
                "total_volume": sum(trade_amounts),
                "avg_trade_amount": sum(trade_amounts) / len(trade_amounts) if trade_amounts else 0,
                "total_profit": sum(trade_profits),
                "avg_profit": sum(trade_profits) / len(trade_profits) if trade_profits else 0,
                "win_rate": len([p for p in trade_profits if p > 0]) / len(trade_profits) if trade_profits else 0,
            }
    
    def get_system_metrics(self) -> Dict:
        """
        Get system metrics summary
        
        Returns:
            Dictionary containing system metrics
        """
        uptime = datetime.now() - self.start_time
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_hours": uptime.total_seconds() / 3600,
            "start_time": self.start_time.isoformat(),
            "last_reset_time": self.last_reset_time.isoformat(),
        }
    
    def get_all_metrics(self) -> Dict:
        """
        Get all metrics
        
        Returns:
            Dictionary containing all metrics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self.get_system_metrics(),
            "api": self.get_api_metrics(),
            "llm": self.get_llm_metrics(),
            "trading": self.get_trading_metrics(),
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            self.api_response_times.clear()
            self.api_request_counts.clear()
            self.api_error_counts.clear()
            
            self.llm_inference_times.clear()
            self.llm_request_counts = 0
            self.llm_error_counts = 0
            self.llm_token_counts.clear()
            
            self.trade_success_count = 0
            self.trade_failure_count = 0
            self.trade_amounts.clear()
            self.trade_profits.clear()
            
            self.last_reset_time = datetime.now()
            
            logger.info("Metrics reset")
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """
        Calculate percentile of data
        
        Args:
            data: List of values
            percentile: Percentile to calculate (0-100)
        
        Returns:
            Percentile value
        """
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get global metrics collector instance
    
    Returns:
        MetricsCollector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
