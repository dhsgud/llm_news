"""
Configuration module for Market Sentiment Analyzer
Loads settings from environment variables with validation
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = "Market Sentiment Analyzer"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Database Configuration
    database_url: str = "sqlite:///./market_analyzer.db"
    
    # llama.cpp Server Configuration
    llama_cpp_base_url: str = "http://localhost:11434"
    llama_cpp_model_path: Optional[str] = None
    
    # News API Configuration
    news_api_key: str = ""
    news_api_base_url: str = "https://newsapi.org/v2"
    
    # VIX Data API Configuration
    vix_api_key: str = ""
    vix_api_provider: str = "alphavantage"
    
    # Brokerage API Configuration
    # Korea Investment & Securities
    korea_investment_app_key: Optional[str] = None
    korea_investment_app_secret: Optional[str] = None
    korea_investment_base_url: str = "https://openapi.koreainvestment.com:9443"
    korea_investment_account_number: Optional[str] = None
    korea_investment_account_product_code: str = "01"
    use_virtual_trading: bool = True
    
    # Kiwoom Securities (Windows only)
    kiwoom_account_number: Optional[str] = None
    kiwoom_user_id: Optional[str] = None
    kiwoom_app_key: Optional[str] = None
    kiwoom_app_secret: Optional[str] = None
    kiwoom_use_mock: bool = True
    kiwoom_api_delay_ms: int = 200
    kiwoom_log_level: str = "INFO"
    kiwoom_reconnect_attempts: int = 3
    kiwoom_timeout_seconds: int = 30
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False
    
    # CORS Settings
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string into list"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    # Cache Settings
    cache_expiry_hours: int = 1
    news_retention_days: int = 7
    
    # Scheduler Settings
    news_collection_hour: int = 0
    news_collection_minute: int = 0
    
    # Auto Trading Settings
    auto_trading_enabled: bool = False
    max_investment_amount: float = 1000000.0
    risk_level: str = "low"
    stop_loss_threshold: float = 0.05
    
    # LLM Settings
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    llm_timeout: int = 120
    
    # Sentiment Scoring
    positive_score: float = 1.0
    neutral_score: float = 0.0
    negative_score: float = -1.0
    negative_weight: float = 1.5  # Conservative bias
    
    # Signal Thresholds
    buy_threshold: int = 80
    sell_threshold: int = 20
    
    # Security Settings
    api_key_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    encryption_master_key: Optional[str] = None
    require_2fa_for_trading: bool = True
    require_2fa_threshold: float = 5000000.0  # 5M KRW
    audit_log_retention_days: int = 365
    
    # Monitoring and Alerting Settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    alert_email_to: Optional[str] = None
    alert_email_from: Optional[str] = None
    sms_enabled: bool = False
    sms_api_key: Optional[str] = None
    sms_phone_number: Optional[str] = None
    
    # Performance Thresholds
    api_response_time_threshold: float = 5.0  # seconds
    llm_inference_time_threshold: float = 30.0  # seconds
    error_rate_threshold: float = 0.1  # 10%


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Uses lru_cache to ensure settings are loaded only once
    """
    return Settings()


# Convenience function for accessing settings
settings = get_settings()
