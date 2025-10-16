"""
Database models package
Exports all SQLAlchemy models and Pydantic schemas
"""

try:
    from models.news_article import (
        NewsArticle,
        NewsArticleBase,
        NewsArticleCreate,
        NewsArticleUpdate,
        NewsArticleResponse
    )

    from models.sentiment_analysis import (
        SentimentAnalysis,
        SentimentAnalysisBase,
        SentimentAnalysisCreate,
        SentimentAnalysisUpdate,
        SentimentAnalysisResponse,
        SentimentResult,
        SentimentType
    )

    from models.analysis_cache import (
        AnalysisCache,
        AnalysisCacheBase,
        AnalysisCacheCreate,
        AnalysisCacheUpdate,
        AnalysisCacheResponse
    )

    from models.stock_price import (
        StockPrice,
        StockPriceBase,
        StockPriceCreate,
        StockPriceUpdate,
        StockPriceResponse
    )

    from models.stock_news_relation import (
        StockNewsRelation,
        StockNewsRelationBase,
        StockNewsRelationCreate,
        StockNewsRelationUpdate,
        StockNewsRelationResponse
    )

    from models.account_holding import (
        AccountHolding,
        AccountHoldingBase,
        AccountHoldingCreate,
        AccountHoldingUpdate,
        AccountHoldingResponse
    )

    from models.trading_schemas import (
        Order,
        TradeResult,
        OrderRequest,
        OrderResponse
    )

    from models.trade_history import (
        TradeHistory,
        TradeHistoryBase,
        TradeHistoryCreate,
        TradeHistoryUpdate,
        TradeHistoryResponse
    )

    from models.auto_trade_config import (
        AutoTradeConfig,
        AutoTradeConfigBase,
        AutoTradeConfigCreate,
        AutoTradeConfigUpdate,
        AutoTradeConfigResponse
    )

    from models.auto_trading_schemas import (
        TradingConfig,
        Holding,
        Portfolio,
        AutoTradeStatus,
        TradeSignal,
        TradeExecutionRequest,
        TradeExecutionResponse
    )
except ImportError:
    from models.news_article import (
        NewsArticle,
        NewsArticleBase,
        NewsArticleCreate,
        NewsArticleUpdate,
        NewsArticleResponse
    )

    from models.sentiment_analysis import (
        SentimentAnalysis,
        SentimentAnalysisBase,
        SentimentAnalysisCreate,
        SentimentAnalysisUpdate,
        SentimentAnalysisResponse,
        SentimentResult,
        SentimentType
    )

    from models.analysis_cache import (
        AnalysisCache,
        AnalysisCacheBase,
        AnalysisCacheCreate,
        AnalysisCacheUpdate,
        AnalysisCacheResponse
    )

    from models.stock_price import (
        StockPrice,
        StockPriceBase,
        StockPriceCreate,
        StockPriceUpdate,
        StockPriceResponse
    )

    from models.stock_news_relation import (
        StockNewsRelation,
        StockNewsRelationBase,
        StockNewsRelationCreate,
        StockNewsRelationUpdate,
        StockNewsRelationResponse
    )

    from models.account_holding import (
        AccountHolding,
        AccountHoldingBase,
        AccountHoldingCreate,
        AccountHoldingUpdate,
        AccountHoldingResponse
    )

    from models.trading_schemas import (
        Order,
        TradeResult,
        OrderRequest,
        OrderResponse
    )

    from models.trade_history import (
        TradeHistory,
        TradeHistoryBase,
        TradeHistoryCreate,
        TradeHistoryUpdate,
        TradeHistoryResponse
    )

    from models.auto_trade_config import (
        AutoTradeConfig,
        AutoTradeConfigBase,
        AutoTradeConfigCreate,
        AutoTradeConfigUpdate,
        AutoTradeConfigResponse
    )

    from models.auto_trading_schemas import (
        TradingConfig,
        Holding,
        Portfolio,
        AutoTradeStatus,
        TradeSignal,
        TradeExecutionRequest,
        TradeExecutionResponse
    )

__all__ = [
    # NewsArticle models
    "NewsArticle",
    "NewsArticleBase",
    "NewsArticleCreate",
    "NewsArticleUpdate",
    "NewsArticleResponse",
    
    # SentimentAnalysis models
    "SentimentAnalysis",
    "SentimentAnalysisBase",
    "SentimentAnalysisCreate",
    "SentimentAnalysisUpdate",
    "SentimentAnalysisResponse",
    "SentimentResult",
    "SentimentType",
    
    # AnalysisCache models
    "AnalysisCache",
    "AnalysisCacheBase",
    "AnalysisCacheCreate",
    "AnalysisCacheUpdate",
    "AnalysisCacheResponse",
    
    # StockPrice models
    "StockPrice",
    "StockPriceBase",
    "StockPriceCreate",
    "StockPriceUpdate",
    "StockPriceResponse",
    
    # StockNewsRelation models
    "StockNewsRelation",
    "StockNewsRelationBase",
    "StockNewsRelationCreate",
    "StockNewsRelationUpdate",
    "StockNewsRelationResponse",
    
    # AccountHolding models
    "AccountHolding",
    "AccountHoldingBase",
    "AccountHoldingCreate",
    "AccountHoldingUpdate",
    "AccountHoldingResponse",
    
    # Trading schemas
    "Order",
    "TradeResult",
    "OrderRequest",
    "OrderResponse",
    
    # TradeHistory models
    "TradeHistory",
    "TradeHistoryBase",
    "TradeHistoryCreate",
    "TradeHistoryUpdate",
    "TradeHistoryResponse",
    
    # AutoTradeConfig models
    "AutoTradeConfig",
    "AutoTradeConfigBase",
    "AutoTradeConfigCreate",
    "AutoTradeConfigUpdate",
    "AutoTradeConfigResponse",
    
    # Auto-trading schemas
    "TradingConfig",
    "Holding",
    "Portfolio",
    "AutoTradeStatus",
    "TradeSignal",
    "TradeExecutionRequest",
    "TradeExecutionResponse",
]
