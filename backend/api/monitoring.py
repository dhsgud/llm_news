"""
Monitoring API endpoints
Provides access to metrics, logs, and alerts
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime

from services.monitoring import get_metrics_collector
from services.alert_service import get_alert_service, AlertType
from api.security import verify_api_key

router = APIRouter(prefix="/api/monitoring")


@router.get("/metrics")
async def get_metrics(api_key: str = Depends(verify_api_key)):
    """
    Get all system metrics
    
    Returns comprehensive metrics including API, LLM, and trading statistics
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_all_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/metrics/api")
async def get_api_metrics(
    endpoint: Optional[str] = Query(None, description="Specific endpoint to get metrics for"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get API metrics
    
    Args:
        endpoint: Optional specific endpoint to filter by
    
    Returns API performance metrics
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_api_metrics(endpoint)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get API metrics: {str(e)}")


@router.get("/metrics/llm")
async def get_llm_metrics(api_key: str = Depends(verify_api_key)):
    """
    Get LLM inference metrics
    
    Returns LLM performance statistics including inference times and token counts
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_llm_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get LLM metrics: {str(e)}")


@router.get("/metrics/trading")
async def get_trading_metrics(api_key: str = Depends(verify_api_key)):
    """
    Get trading metrics
    
    Returns trading statistics including success rates and profit/loss
    """
    try:
        collector = get_metrics_collector()
        metrics = collector.get_trading_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trading metrics: {str(e)}")


@router.post("/metrics/reset")
async def reset_metrics(api_key: str = Depends(verify_api_key)):
    """
    Reset all metrics
    
    Clears all collected metrics and resets counters
    """
    try:
        collector = get_metrics_collector()
        collector.reset_metrics()
        return {"message": "Metrics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset metrics: {str(e)}")


@router.get("/alerts")
async def get_alerts(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts to return"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    api_key: str = Depends(verify_api_key)
):
    """
    Get alert history
    
    Args:
        limit: Maximum number of alerts to return
        alert_type: Optional filter by alert type
    
    Returns list of recent alerts
    """
    try:
        alert_service = get_alert_service()
        
        # Convert string to AlertType enum if provided
        alert_type_enum = None
        if alert_type:
            try:
                alert_type_enum = AlertType(alert_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid alert type: {alert_type}")
        
        alerts = alert_service.get_alert_history(limit=limit, alert_type=alert_type_enum)
        return {"alerts": alerts, "count": len(alerts)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/alerts/stats")
async def get_alert_stats(api_key: str = Depends(verify_api_key)):
    """
    Get alert statistics
    
    Returns summary statistics about alerts
    """
    try:
        alert_service = get_alert_service()
        stats = alert_service.get_alert_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get alert stats: {str(e)}")


@router.get("/health/detailed")
async def detailed_health_check():
    """
    Detailed health check with component status
    
    Returns health status of all system components
    """
    from app.database import engine
    from sqlalchemy import text
    from services.llm_client import LlamaCppClient
    
    health_status = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "components": {}
    }
    
    # Check database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        health_status["overall_status"] = "degraded"
    
    # Check LLM service
    try:
        client = LlamaCppClient()
        health_status["components"]["llm"] = {
            "status": "healthy",
            "message": "LLM service connected"
        }
    except Exception as e:
        health_status["components"]["llm"] = {
            "status": "unhealthy",
            "message": str(e)
        }
        health_status["overall_status"] = "degraded"
    
    # Check metrics collector
    try:
        collector = get_metrics_collector()
        system_metrics = collector.get_system_metrics()
        health_status["components"]["metrics"] = {
            "status": "healthy",
            "uptime_hours": system_metrics["uptime_hours"]
        }
    except Exception as e:
        health_status["components"]["metrics"] = {
            "status": "unhealthy",
            "message": str(e)
        }
    
    # Check alert service
    try:
        alert_service = get_alert_service()
        health_status["components"]["alerts"] = {
            "status": "healthy",
            "total_alerts": len(alert_service.alert_history)
        }
    except Exception as e:
        health_status["components"]["alerts"] = {
            "status": "unhealthy",
            "message": str(e)
        }
    
    return health_status
