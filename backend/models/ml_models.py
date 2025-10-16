"""
Machine Learning Models for Trading Pattern Analysis
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Text
from pydantic import BaseModel, Field
from app.database import Base


# SQLAlchemy Models
class TradePattern(Base):
    """거래 ?�턴 ?�??""
    __tablename__ = "trade_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_type = Column(String(50), nullable=False)  # 'winning', 'losing', 'neutral'
    symbol = Column(String(20), nullable=False, index=True)
    entry_signal_score = Column(Float, nullable=False)
    exit_signal_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=False)
    vix_level = Column(Float, nullable=True)
    holding_period_hours = Column(Float, nullable=False)
    profit_loss_percent = Column(Float, nullable=False)
    trade_size = Column(Float, nullable=False)
    market_condition = Column(String(20), nullable=True)
    features = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class LearnedStrategy(Base):
    """?�습???�략 ?�라미터"""
    __tablename__ = "learned_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String(100), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    buy_threshold = Column(Float, nullable=False)
    sell_threshold = Column(Float, nullable=False)
    position_size_multiplier = Column(Float, nullable=False, default=1.0)
    stop_loss_percent = Column(Float, nullable=False)
    take_profit_percent = Column(Float, nullable=True)
    max_holding_hours = Column(Float, nullable=True)
    vix_adjustment_factor = Column(Float, nullable=False, default=1.0)
    parameters = Column(JSON, nullable=True)
    performance_metrics = Column(JSON, nullable=True)
    training_samples = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class LearningSession(Base):
    """?�습 ?�션 기록"""
    __tablename__ = "learning_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_type = Column(String(50), nullable=False)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='running')
    trades_analyzed = Column(Integer, nullable=False, default=0)
    patterns_extracted = Column(Integer, nullable=False, default=0)
    insights = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# Pydantic Schemas
class TradePatternCreate(BaseModel):
    """거래 ?�턴 ?�성 ?�키�?""
    pattern_type: str = Field(..., description="Pattern type: winning, losing, neutral")
    symbol: str
    entry_signal_score: float
    exit_signal_score: Optional[float] = None
    sentiment_score: float
    vix_level: Optional[float] = None
    holding_period_hours: float
    profit_loss_percent: float
    trade_size: float
    market_condition: Optional[str] = None
    features: Optional[Dict[str, Any]] = None


class TradePatternResponse(BaseModel):
    """거래 ?�턴 ?�답 ?�키�?""
    id: int
    pattern_type: str
    symbol: str
    entry_signal_score: float
    exit_signal_score: Optional[float]
    sentiment_score: float
    vix_level: Optional[float]
    holding_period_hours: float
    profit_loss_percent: float
    trade_size: float
    market_condition: Optional[str]
    features: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class LearnedStrategyResponse(BaseModel):
    """?�습???�략 ?�답 ?�키�?""
    id: int
    strategy_name: str
    version: int
    buy_threshold: float
    sell_threshold: float
    position_size_multiplier: float
    stop_loss_percent: float
    take_profit_percent: Optional[float]
    max_holding_hours: Optional[float]
    vix_adjustment_factor: float
    parameters: Optional[Dict[str, Any]]
    performance_metrics: Optional[Dict[str, Any]]
    training_samples: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LearningSessionResponse(BaseModel):
    """?�습 ?�션 ?�답 ?�키�?""
    id: int
    session_type: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    trades_analyzed: int
    patterns_extracted: int
    insights: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PatternAnalysisRequest(BaseModel):
    """?�턴 분석 ?�청 ?�키�?""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_trades: int = Field(default=10, description="Minimum trades to analyze")
    symbols: Optional[list[str]] = None


class StrategyOptimizationRequest(BaseModel):
    """?�략 최적???�청 ?�키�?""
    strategy_name: str = Field(default="sentiment_based_v1")
    min_profit_threshold: float = Field(default=2.0, description="Minimum profit % to consider winning")
    optimization_metric: str = Field(default="sharpe_ratio", description="Metric to optimize")


class PatternInsights(BaseModel):
    """?�턴 분석 ?�사?�트"""
    total_patterns: int
    winning_patterns: int
    losing_patterns: int
    avg_winning_profit: float
    avg_losing_loss: float
    win_rate: float
    best_entry_score_range: tuple[float, float]
    best_sentiment_range: tuple[float, float]
    optimal_holding_hours: float
    recommendations: list[str]
