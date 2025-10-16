"""
Custom Exception Classes and Global Exception Handlers

Provides custom exceptions and centralized error handling for the API.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


# Custom Exception Classes

class APIException(Exception):
    """
    Base exception for API errors
    """
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or "API_ERROR"
        self.headers = headers
        super().__init__(detail)


class DatabaseError(APIException):
    """
    Exception for database-related errors
    """
    def __init__(self, detail: str, original_error: Optional[Exception] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {detail}",
            error_code="DATABASE_ERROR"
        )
        self.original_error = original_error


class LLMServiceError(APIException):
    """
    Exception for LLM service errors
    """
    def __init__(self, detail: str, original_error: Optional[Exception] = None):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM service error: {detail}",
            error_code="LLM_SERVICE_ERROR"
        )
        self.original_error = original_error


class InsufficientDataError(APIException):
    """
    Exception for insufficient data scenarios
    """
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient data: {detail}",
            error_code="INSUFFICIENT_DATA"
        )


class CacheError(APIException):
    """
    Exception for cache-related errors
    """
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache error: {detail}",
            error_code="CACHE_ERROR"
        )


class ExternalAPIError(APIException):
    """
    Exception for external API errors (News API, VIX API, etc.)
    """
    def __init__(self, service: str, detail: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{service} API error: {detail}",
            error_code="EXTERNAL_API_ERROR"
        )


# Global Exception Handlers

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Handler for custom APIException
    """
    logger.error(
        f"API Exception: {exc.error_code} - {exc.detail}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "detail": exc.detail,
            "path": request.url.path,
            "timestamp": str(request.state.start_time) if hasattr(request.state, "start_time") else None
        },
        headers=exc.headers
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handler for request validation errors
    """
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "detail": "Request validation failed",
            "errors": exc.errors(),
            "path": request.url.path
        }
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handler for SQLAlchemy database errors
    """
    logger.error(
        f"Database error: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DATABASE_ERROR",
            "detail": "A database error occurred. Please try again later.",
            "path": request.url.path
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler for unhandled exceptions
    """
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "detail": "An unexpected error occurred. Please try again later.",
            "path": request.url.path
        }
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(APIException, api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers registered")
