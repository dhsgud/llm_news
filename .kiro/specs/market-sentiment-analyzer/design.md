# Design Document

## Overview

Market Sentiment Analyzer는 AI 기반 금융 뉴스 감성 분석 및 자동 매매 시스템입니다. Apriel-1.5-15b-Thinker 모델을 활용하여 뉴스를 분석하고, 보수적인 투자 추천을 제공하며, 향후 증권사 API 연동을 통한 자동 매매까지 지원합니다.

### 핵심 기능
- 일주일간 금융 뉴스 자동 수집 및 감성 분석
- 3단계 프롬프트 체인을 통한 정교한 시장 동향 분석
- VIX 기반 보수적 매수/매도 비율 추천
- 증권사 API 연동을 통한 실시간 주식 데이터 수집
- 데이터 기반 자동 매매 시스템
- 직관적인 원클릭 웹 인터페이스

### 기술 스택
- **Backend**: Python 3.10+, FastAPI
- **LLM**: llama.cpp server (Apriel-1.5-15b-Thinker-Q8_0.gguf)
- **Database**: PostgreSQL (production) / SQLite (development)
- **Cache**: Redis (optional)
- **Frontend**: React 18, Tailwind CSS, Chart.js
- **Scheduler**: APScheduler
- **API Integration**: 한국투자증권 API, 키움증권 API

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Frontend (React)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Market View  │  │ Stock View   │  │ Auto Trading │          │
│  │ Dashboard    │  │ Dashboard    │  │ Dashboard    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
┌────────────────────────────┴────────────────────────────────────┐
│                    FastAPI Backend Server                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    API Endpoints                          │   │
│  │  /analyze  /stocks  /trades  /auto-trade/config          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ News Fetcher │  │ LLM Analyzer │  │ Signal Gen   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐          │
│  │ Brokerage    │  │ Auto Trading │  │ Risk Manager │          │
│  │ Connector    │  │ Engine       │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────┬──────────────┬──────────────┬─────────────────────┘
             │              │              │
             │              │              │
    ┌────────┴────┐  ┌─────┴─────┐  ┌─────┴─────┐
    │ PostgreSQL  │  │llama.cpp  │  │ External  │
    │  Database   │  │  Server   │  │   APIs    │
    │             │  │  (Local)  │  │ (News/VIX)│
    └─────────────┘  └───────────┘  └───────────┘
                                      │ Brokerage │
                                      │    API    │
                                      └───────────┘
```

### Data Flow

#### Phase 1: News Collection & Analysis (Background)
```
News API → News Fetcher → Database (news_articles)
                ↓
        LLM Analyzer (Step 1: Individual Analysis)
                ↓
        Database (sentiment_analysis)
```

#### Phase 2: User Request Flow
```
User Click → Frontend → /analyze API
                ↓
        Signal Generator
                ↓
        LLM Analyzer (Step 2 & 3: Aggregation & Recommendation)
                ↓
        Calculate Buy/Sell Ratio
                ↓
        Frontend (Display Results)
```

#### Phase 3: Auto Trading Flow (Future)
```
Signal Generator → Auto Trading Engine
                ↓
        Risk Manager (Validate)
                ↓
        Brokerage API (Execute Order)
                ↓
        Database (trade_history)
                ↓
        Notification Service
```

## Components and Interfaces

### 1. Backend Core Modules

#### 1.1 News Fetcher (`news_fetcher.py`)

**책임**: 외부 뉴스 API에서 금융 뉴스를 주기적으로 수집

**주요 클래스**:
```python
class NewsAPIClient:
    def __init__(self, api_key: str, sources: List[str])
    def fetch_news(self, query: str, from_date: datetime, to_date: datetime) -> List[NewsArticle]
    def filter_financial_news(self, articles: List[NewsArticle]) -> List[NewsArticle]

class NewsScheduler:
    def __init__(self, db_session, news_client: NewsAPIClient)
    def schedule_daily_collection(self)
    def collect_and_store(self)
    def cleanup_old_news(self, days: int = 7)
```

**인터페이스**:
- Input: News API credentials, search queries
- Output: NewsArticle objects stored in database
- Schedule: Daily at 00:00 KST

#### 1.2 LLM Analyzer (`llm_analyzer.py`)

**책임**: llama.cpp 서버와 통신하여 3단계 프롬프트 체인 실행

**주요 클래스**:
```python
class LlamaCppClient:
    def __init__(self, base_url: str = "http://localhost:8080", model_path: str = None)
    def generate(self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 2048) -> str
    def generate_json(self, prompt: str, system_prompt: str = None) -> dict
    # llama.cpp의 /completion 엔드포인트 사용

class SentimentAnalyzer:
    def __init__(self, llama_client: LlamaCppClient)
    def analyze_article(self, article: NewsArticle) -> SentimentResult
    # Step 1: Individual article analysis
    
class TrendAggregator:
    def __init__(self, llama_client: LlamaCppClient)
    def aggregate_weekly_trend(self, sentiments: List[SentimentResult]) -> TrendSummary
    # Step 2: Weekly trend aggregation

class RecommendationEngine:
    def __init__(self, llama_client: LlamaCppClient)
    def generate_recommendation(self, trend: TrendSummary, vix: float) -> Recommendation
    # Step 3: Conservative buy/sell recommendation
```

**프롬프트 템플릿**:
```python
STEP1_SYSTEM_PROMPT = """
당신은 특정 금융 자산에 대한 뉴스 기사의 감성을 분석하는 전문 금융 분석가입니다.
"""

STEP2_SYSTEM_PROMPT = """
당신은 시장 전략가입니다. 일주일간의 개별 뉴스 감성 분석 데이터가 주어질 것입니다.
"""

STEP3_SYSTEM_PROMPT = """
당신은 보수적이고 리스크를 회피하는 성향의 포트폴리오 매니저입니다.
부정적인 뉴스와 높은 불확실성을 다른 요인보다 더 무겁게 가중하여 판단해야 합니다.
"""
```

#### 1.3 Signal Generator (`signal_generator.py`)

**책임**: 감성 데이터를 정량화하고 최종 매수/매도 비율 계산

**주요 클래스**:
```python
class SentimentQuantifier:
    POSITIVE_SCORE = 1.0
    NEUTRAL_SCORE = 0.0
    NEGATIVE_SCORE = -1.0
    NEGATIVE_WEIGHT = 1.5  # Conservative bias
    
    def quantify(self, sentiment: str) -> float
    def calculate_daily_score(self, articles: List[SentimentResult]) -> float

class VIXFetcher:
    def __init__(self, api_key: str)
    def get_current_vix(self) -> float
    def normalize_vix(self, vix: float) -> float  # 0-1 range

class SignalCalculator:
    def __init__(self, quantifier: SentimentQuantifier, vix_fetcher: VIXFetcher)
    def calculate_weekly_signal(self, daily_scores: List[float], vix_values: List[float]) -> float
    def normalize_to_ratio(self, signal_score: float) -> int  # 0-100
    
    # Formula: Weekly_Signal = Σ(Daily_Score × (1 + VIX_Normalized))
    # Normalization: Sigmoid or Rolling Window
```

#### 1.4 Brokerage Connector (`brokerage_connector.py`)

**책임**: 증권사 API와 통신하여 실시간 데이터 수집 및 주문 실행

**주요 클래스**:
```python
class BrokerageAPIBase(ABC):
    @abstractmethod
    def authenticate(self, credentials: dict) -> bool
    @abstractmethod
    def get_stock_price(self, symbol: str) -> StockPrice
    @abstractmethod
    def get_account_balance(self) -> AccountInfo
    @abstractmethod
    def place_order(self, order: Order) -> OrderResult

class KoreaInvestmentAPI(BrokerageAPIBase):
    # 한국투자증권 API 구현
    
class KiwoomAPI(BrokerageAPIBase):
    # 키움증권 API 구현

class StockDataCollector:
    def __init__(self, broker_api: BrokerageAPIBase)
    def collect_realtime_prices(self, symbols: List[str])
    def sync_account_holdings(self)
    def filter_news_by_stock(self, symbol: str) -> List[NewsArticle]
```

#### 1.5 Auto Trading Engine (`auto_trading_engine.py`)

**책임**: 자동 매매 로직 실행 및 리스크 관리

**주요 클래스**:
```python
class TradingConfig:
    max_investment: float
    risk_level: str  # 'low', 'medium', 'high'
    trading_hours: Tuple[time, time]
    stop_loss_threshold: float
    buy_threshold: int = 80  # Buy if ratio >= 80
    sell_threshold: int = 20  # Sell if ratio <= 20

class RiskManager:
    def __init__(self, config: TradingConfig)
    def validate_trade(self, order: Order, current_portfolio: Portfolio) -> bool
    def calculate_position_size(self, signal_ratio: int, available_cash: float) -> float
    def check_stop_loss(self, holdings: List[Holding]) -> List[Order]

class AutoTradingEngine:
    def __init__(self, broker_api: BrokerageAPIBase, risk_manager: RiskManager)
    def execute_signal(self, symbol: str, signal_ratio: int)
    def monitor_positions(self)
    def emergency_stop(self)
```

### 2. API Endpoints

#### 2.1 Market Analysis Endpoints
```python
@app.post("/api/analyze")
async def analyze_market(asset_type: str = "general"):
    """
    전체 시장 또는 특정 자산 유형의 감성 분석 실행
    Response: {
        "buy_sell_ratio": int,
        "trend_summary": str,
        "last_updated": datetime,
        "vix": float
    }
    """

@app.get("/api/news")
async def get_recent_news(days: int = 7, sentiment: str = None):
    """
    최근 뉴스 목록 조회
    """

@app.get("/api/sentiment/daily")
async def get_daily_sentiment(days: int = 7):
    """
    일별 감성 점수 조회 (차트용)
    """
```

#### 2.2 Stock Data Endpoints
```python
@app.get("/api/stocks/{symbol}")
async def get_stock_info(symbol: str):
    """
    특정 종목 정보 및 관련 뉴스
    """

@app.get("/api/stocks/{symbol}/sentiment")
async def get_stock_sentiment(symbol: str):
    """
    종목별 감성 분석 결과
    """

@app.get("/api/account/holdings")
async def get_holdings():
    """
    현재 보유 종목 조회
    """
```

#### 2.3 Auto Trading Endpoints
```python
@app.post("/api/auto-trade/config")
async def update_trading_config(config: TradingConfig):
    """
    자동 매매 설정 업데이트
    """

@app.post("/api/auto-trade/start")
async def start_auto_trading():
    """
    자동 매매 시작
    """

@app.post("/api/auto-trade/stop")
async def stop_auto_trading():
    """
    자동 매매 중지
    """

@app.get("/api/trades/history")
async def get_trade_history(limit: int = 50):
    """
    거래 내역 조회
    """
```

## Data Models

### Database Schema

```sql
-- 뉴스 기사
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    published_date TIMESTAMP NOT NULL,
    source VARCHAR(100),
    url VARCHAR(500),
    asset_type VARCHAR(50),  -- 'stock', 'crypto', 'general'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_published_date (published_date),
    INDEX idx_asset_type (asset_type)
);

-- 감성 분석 결과
CREATE TABLE sentiment_analysis (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES news_articles(id),
    sentiment VARCHAR(20) NOT NULL,  -- 'Positive', 'Negative', 'Neutral'
    score FLOAT NOT NULL,  -- -1.5 to 1.0
    reasoning TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_article_id (article_id),
    INDEX idx_analyzed_at (analyzed_at)
);

-- 분석 캐시
CREATE TABLE analysis_cache (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(100) UNIQUE NOT NULL,
    result_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    INDEX idx_cache_key (cache_key),
    INDEX idx_expires_at (expires_at)
);

-- 주식 가격 데이터
CREATE TABLE stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    volume BIGINT,
    open_price DECIMAL(10, 2),
    high_price DECIMAL(10, 2),
    low_price DECIMAL(10, 2),
    timestamp TIMESTAMP NOT NULL,
    INDEX idx_symbol_timestamp (symbol, timestamp)
);

-- 종목-뉴스 연관
CREATE TABLE stock_news_relation (
    id SERIAL PRIMARY KEY,
    stock_symbol VARCHAR(20) NOT NULL,
    article_id INTEGER REFERENCES news_articles(id),
    relevance_score FLOAT,
    INDEX idx_stock_symbol (stock_symbol),
    INDEX idx_article_id (article_id)
);

-- 계좌 보유 종목
CREATE TABLE account_holdings (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    average_price DECIMAL(10, 2) NOT NULL,
    current_price DECIMAL(10, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_symbol (symbol)
);

-- 거래 내역
CREATE TABLE trade_history (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    trade_type VARCHAR(10) NOT NULL,  -- 'BUY', 'SELL'
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL,
    signal_ratio INTEGER,
    reasoning TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_auto_trade BOOLEAN DEFAULT FALSE,
    INDEX idx_symbol (symbol),
    INDEX idx_executed_at (executed_at)
);

-- 자동 매매 설정
CREATE TABLE auto_trade_config (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    max_investment DECIMAL(12, 2) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    trading_start_time TIME,
    trading_end_time TIME,
    stop_loss_threshold FLOAT,
    buy_threshold INTEGER DEFAULT 80,
    sell_threshold INTEGER DEFAULT 20,
    is_active BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Python Data Models (Pydantic)

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class NewsArticle(BaseModel):
    id: Optional[int]
    title: str
    content: str
    published_date: datetime
    source: str
    url: Optional[str]
    asset_type: str = "general"

class SentimentResult(BaseModel):
    article_id: int
    sentiment: str  # 'Positive', 'Negative', 'Neutral'
    score: float
    reasoning: str
    analyzed_at: datetime

class TrendSummary(BaseModel):
    summary_text: str
    dominant_sentiment: str
    key_drivers: List[str]
    period_start: datetime
    period_end: datetime

class Recommendation(BaseModel):
    buy_sell_ratio: int  # 0-100
    trend_summary: str
    vix: float
    last_updated: datetime
    confidence: str  # 'low', 'medium', 'high'

class StockPrice(BaseModel):
    symbol: str
    price: float
    volume: int
    open_price: float
    high_price: float
    low_price: float
    timestamp: datetime

class Order(BaseModel):
    symbol: str
    trade_type: str  # 'BUY', 'SELL'
    quantity: int
    price: Optional[float]
    order_type: str = "MARKET"  # 'MARKET', 'LIMIT'

class TradeResult(BaseModel):
    order_id: str
    symbol: str
    trade_type: str
    quantity: int
    executed_price: float
    total_amount: float
    executed_at: datetime
    status: str  # 'SUCCESS', 'FAILED', 'PENDING'
```

## Error Handling

### Error Handling Strategy

#### 1. API Level Errors
```python
class APIException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
    )
```

#### 2. External Service Errors
- **Ollama Server Down**: Retry 3 times with exponential backoff, then return cached result
- **News API Failure**: Log error, skip current cycle, retry next scheduled time
- **Brokerage API Failure**: Immediately stop auto-trading, send alert notification
- **Database Connection Loss**: Implement connection pooling with auto-reconnect

#### 3. Trading Safety Mechanisms
```python
class TradingSafetyCheck:
    def validate_before_trade(self, order: Order) -> Tuple[bool, str]:
        # Check 1: Market hours
        # Check 2: Sufficient balance
        # Check 3: Position size limits
        # Check 4: Daily loss limit
        # Check 5: Abnormal market conditions (circuit breaker)
        pass
```

### Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/app.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)

# Separate loggers for different components
news_logger = logging.getLogger('news_fetcher')
llm_logger = logging.getLogger('llm_analyzer')
trading_logger = logging.getLogger('auto_trading')
```

## Testing Strategy

### 1. Unit Tests
- **LLM Analyzer**: Mock llama.cpp responses, test prompt generation
- **Signal Calculator**: Test quantification formulas with known inputs
- **Risk Manager**: Test position sizing and stop-loss logic

### 2. Integration Tests
- **API Endpoints**: Test full request-response cycle
- **Database Operations**: Test CRUD operations with test database
- **llama.cpp Integration**: Test with actual local llama.cpp server

### 3. End-to-End Tests
- **News Collection Flow**: Mock News API, verify database storage
- **Analysis Flow**: Test complete 3-step prompt chain
- **Auto Trading Flow**: Use paper trading mode with mock brokerage API

### 4. Safety Tests
- **Trading Limits**: Verify max investment and position size limits
- **Stop Loss**: Test automatic stop-loss execution
- **Emergency Stop**: Test manual and automatic emergency stop

### Test Data
```python
# Mock sentiment data for testing
MOCK_SENTIMENTS = [
    {"date": "2025-10-01", "score": 0.5, "sentiment": "Positive"},
    {"date": "2025-10-02", "score": -1.5, "sentiment": "Negative"},
    # ... 7 days of data
]

# Mock VIX values
MOCK_VIX = {"value": 18.5, "normalized": 0.37}
```

## Deployment Considerations

### Development Environment
```bash
# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# llama.cpp server
# Download model: Apriel-1.5-15b-Thinker-Q8_0.gguf
# Start server: ./server -m models/Apriel-1.5-15b-Thinker-Q8_0.gguf -c 4096 --port 8080

# Database
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15

# Frontend
cd frontend
npm install
npm run dev
```

### Production Deployment
- **Backend**: Docker container with Gunicorn + Uvicorn workers
- **Database**: Managed PostgreSQL (AWS RDS, Google Cloud SQL)
- **llama.cpp**: Dedicated GPU server or cloud GPU instance (CUDA/Metal support)
- **Frontend**: Static hosting (Vercel, Netlify) or Nginx
- **Monitoring**: Prometheus + Grafana for metrics
- **Alerts**: Email/SMS notifications for trading events

### Environment Variables
```bash
# .env file
DATABASE_URL=postgresql://user:password@localhost:5432/market_analyzer
LLAMA_CPP_BASE_URL=http://localhost:8080
LLAMA_CPP_MODEL_PATH=/path/to/Apriel-1.5-15b-Thinker-Q8_0.gguf
NEWS_API_KEY=your_news_api_key
VIX_API_KEY=your_vix_api_key
KOREA_INVESTMENT_APP_KEY=your_app_key
KOREA_INVESTMENT_APP_SECRET=your_app_secret
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

## Security Considerations

### 1. API Security
- Use API keys for authentication
- Implement rate limiting (100 requests/minute per IP)
- HTTPS only in production
- CORS configuration for frontend domain

### 2. Trading Security
- Encrypt brokerage API credentials
- Two-factor authentication for auto-trading activation
- Transaction signing for order execution
- Audit log for all trading activities

### 3. Data Protection
- Hash sensitive user data
- Regular database backups
- Secure storage of API keys (environment variables, not in code)

## Performance Optimization

### 1. Caching Strategy
- Cache analysis results for 1 hour
- Cache stock prices for 1 minute
- Use Redis for distributed caching

### 2. Database Optimization
- Index on frequently queried columns
- Partition trade_history table by date
- Archive old data (>1 year) to separate table

### 3. LLM Optimization
- Batch process articles when possible
- Use streaming responses for long outputs
- Implement request queuing to avoid overload

## Future Enhancements

### Phase 1 (Current): Basic Analysis
- News collection and sentiment analysis
- Manual market analysis via web UI

### Phase 2: Stock Integration
- Brokerage API integration
- Real-time stock data collection
- Stock-specific sentiment analysis

### Phase 3: Auto Trading
- Automated buy/sell execution
- Risk management system
- Performance tracking dashboard

### Phase 4: Advanced Features
- Multi-asset support (crypto, forex)
- Machine learning model training on historical trades
- Portfolio optimization algorithms
- Social sentiment analysis (Twitter, Reddit)
- Backtesting framework
