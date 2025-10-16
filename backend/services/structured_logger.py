"""
Structured Logging Service
Provides JSON-formatted logging with context and metadata
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON
        
        Args:
            record: Log record to format
        
        Returns:
            JSON-formatted log string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Add process and thread info
        log_data["process_id"] = record.process
        log_data["thread_id"] = record.thread
        
        return json.dumps(log_data)


class StructuredLogger:
    """
    Structured logger with context support
    """
    
    def __init__(self, name: str, log_dir: str = "logs"):
        """
        Initialize structured logger
        
        Args:
            name: Logger name
            log_dir: Directory for log files
        """
        self.logger = logging.getLogger(name)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Don't add handlers if already configured
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup log handlers"""
        # JSON file handler (rotating by size)
        json_handler = RotatingFileHandler(
            self.log_dir / "app.json.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        json_handler.setFormatter(JSONFormatter())
        json_handler.setLevel(logging.DEBUG)
        
        # Error file handler (rotating daily)
        error_handler = TimedRotatingFileHandler(
            self.log_dir / "error.log",
            when="midnight",
            interval=1,
            backupCount=30
        )
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        error_handler.setLevel(logging.ERROR)
        
        # Access log handler (rotating daily)
        access_handler = TimedRotatingFileHandler(
            self.log_dir / "access.log",
            when="midnight",
            interval=1,
            backupCount=30
        )
        access_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        access_handler.setLevel(logging.INFO)
        
        self.logger.addHandler(json_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(access_handler)
    
    def _log_with_context(self, level: int, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Log message with context
        
        Args:
            level: Log level
            message: Log message
            context: Additional context data
            **kwargs: Additional keyword arguments
        """
        extra_fields = context or {}
        extra_fields.update(kwargs)
        
        # Create log record with extra fields
        extra = {"extra_fields": extra_fields}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log debug message"""
        self._log_with_context(logging.DEBUG, message, context, **kwargs)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log info message"""
        self._log_with_context(logging.INFO, message, context, **kwargs)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log warning message"""
        self._log_with_context(logging.WARNING, message, context, **kwargs)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log error message"""
        self._log_with_context(logging.ERROR, message, context, **kwargs)
    
    def critical(self, message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        """Log critical message"""
        self._log_with_context(logging.CRITICAL, message, context, **kwargs)
    
    def log_api_request(self, method: str, path: str, status_code: int, response_time: float, 
                       user_id: Optional[str] = None, **kwargs):
        """
        Log API request
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            response_time: Response time in seconds
            user_id: User ID if authenticated
            **kwargs: Additional context
        """
        context = {
            "event_type": "api_request",
            "method": method,
            "path": path,
            "status_code": status_code,
            "response_time": response_time,
        }
        
        if user_id:
            context["user_id"] = user_id
        
        context.update(kwargs)
        
        self.info(f"{method} {path} - {status_code} - {response_time:.3f}s", context)
    
    def log_llm_inference(self, prompt_type: str, inference_time: float, token_count: Optional[int] = None,
                         success: bool = True, error: Optional[str] = None, **kwargs):
        """
        Log LLM inference
        
        Args:
            prompt_type: Type of prompt (e.g., "sentiment_analysis", "trend_summary")
            inference_time: Inference time in seconds
            token_count: Number of tokens generated
            success: Whether inference was successful
            error: Error message if failed
            **kwargs: Additional context
        """
        context = {
            "event_type": "llm_inference",
            "prompt_type": prompt_type,
            "inference_time": inference_time,
            "success": success,
        }
        
        if token_count:
            context["token_count"] = token_count
        
        if error:
            context["error"] = error
        
        context.update(kwargs)
        
        level = logging.INFO if success else logging.ERROR
        message = f"LLM inference: {prompt_type} - {inference_time:.3f}s"
        if not success:
            message += f" - FAILED: {error}"
        
        self._log_with_context(level, message, context)
    
    def log_trade(self, action: str, symbol: str, quantity: int, price: float,
                 success: bool = True, error: Optional[str] = None, **kwargs):
        """
        Log trading action
        
        Args:
            action: Trade action (buy/sell)
            symbol: Stock symbol
            quantity: Number of shares
            price: Price per share
            success: Whether trade was successful
            error: Error message if failed
            **kwargs: Additional context
        """
        context = {
            "event_type": "trade",
            "action": action,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "total_amount": quantity * price,
            "success": success,
        }
        
        if error:
            context["error"] = error
        
        context.update(kwargs)
        
        level = logging.INFO if success else logging.ERROR
        message = f"Trade: {action} {quantity} {symbol} @ {price}"
        if not success:
            message += f" - FAILED: {error}"
        
        self._log_with_context(level, message, context)
    
    def log_system_event(self, event_type: str, message: str, severity: str = "info", **kwargs):
        """
        Log system event
        
        Args:
            event_type: Type of event (e.g., "startup", "shutdown", "error")
            message: Event message
            severity: Event severity (debug/info/warning/error/critical)
            **kwargs: Additional context
        """
        context = {
            "event_type": f"system_{event_type}",
        }
        context.update(kwargs)
        
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }
        
        level = level_map.get(severity.lower(), logging.INFO)
        self._log_with_context(level, message, context)


# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}


def get_structured_logger(name: str = "app") -> StructuredLogger:
    """
    Get or create structured logger instance
    
    Args:
        name: Logger name
    
    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]
