"""
Main FastAPI application entry point
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time

from config import settings
from app.database import init_db, close_db
from api import market_router, stock_router
from api.auto_trading import router as auto_trading_router
from api.cache import router as cache_router
from api.database_maintenance import router as maintenance_router
from api.security import router as security_router
from api.exceptions import register_exception_handlers

# Configure logging
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging with file and console handlers
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Start cache maintenance scheduler
    try:
        from services.cache_scheduler import start_cache_scheduler
        start_cache_scheduler()
        logger.info("Cache scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start cache scheduler: {e}")
    
    # Start archiving scheduler
    try:
        from services.archiving_scheduler import start_archiving_scheduler
        start_archiving_scheduler()
        logger.info("Archiving scheduler started")
    except Exception as e:
        logger.warning(f"Failed to start archiving scheduler: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    
    # Stop cache scheduler
    try:
        from services.cache_scheduler import stop_cache_scheduler
        stop_cache_scheduler()
        logger.info("Cache scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping cache scheduler: {e}")
    
    # Stop archiving scheduler
    try:
        from services.archiving_scheduler import stop_archiving_scheduler
        stop_archiving_scheduler()
        logger.info("Archiving scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping archiving scheduler: {e}")
    
    try:
        close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# Register exception handlers
register_exception_handlers(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing and monitoring middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """
    Middleware to add processing time to response headers and record metrics
    """
    start_time = time.time()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        # Record API metrics
        try:
            from services.monitoring import get_metrics_collector
            collector = get_metrics_collector()
            collector.record_api_request(
                endpoint=request.url.path,
                response_time=process_time,
                success=response.status_code < 400
            )
        except Exception as e:
            logger.debug(f"Failed to record API metrics: {e}")
        
        logger.debug(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        
        # Record failed request
        try:
            from services.monitoring import get_metrics_collector
            collector = get_metrics_collector()
            collector.record_api_request(
                endpoint=request.url.path,
                response_time=process_time,
                success=False
            )
        except:
            pass
        
        raise


# Include routers
app.include_router(security_router, tags=["security"])
app.include_router(market_router, prefix="/api", tags=["market"])
app.include_router(stock_router, prefix="/api", tags=["stock"])
app.include_router(auto_trading_router, prefix="/api", tags=["auto-trading"])
app.include_router(cache_router, prefix="/api", tags=["cache"])
app.include_router(maintenance_router, tags=["maintenance"])

# Import and include monitoring router
from api.monitoring import router as monitoring_router
app.include_router(monitoring_router, tags=["monitoring"])

# Import and include ML learning router
# Temporarily commented out due to encoding issues
# from api.ml_learning import router as ml_router
# app.include_router(ml_router, tags=["ml-learning"])

# Import and include backtest router
# Temporarily commented out due to missing numpy dependency
# from api.backtest import router as backtest_router
# app.include_router(backtest_router, tags=["backtesting"])

# Import and include multi-asset router
# from api.multi_asset import router as multi_asset_router
# app.include_router(multi_asset_router, tags=["multi-asset"])

# Import and include social sentiment router
from api.social_sentiment import router as social_sentiment_router
app.include_router(social_sentiment_router, tags=["social-sentiment"])

# Import and include news collection router
from api.news_collection import router as news_collection_router
app.include_router(news_collection_router, tags=["news"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    from services.llm_client import LlamaCppClient
    
    # Check database
    db_status = "healthy"
    try:
        from app.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(f"Database health check failed: {e}")
    
    # Check llama.cpp server
    llm_status = "healthy"
    try:
        client = LlamaCppClient()
        # Simple connectivity check
        llm_status = "connected"
    except Exception as e:
        llm_status = f"unhealthy: {str(e)}"
        logger.error(f"LLM health check failed: {e}")
    
    return {
        "status": "healthy" if db_status == "healthy" and "connected" in llm_status else "degraded",
        "database": db_status,
        "llama_cpp": llm_status,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
