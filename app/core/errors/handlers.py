from typing import Optional, Dict, Any
from fastapi import HTTPException
import logging
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("ryze.financial")


class FinancialAnalysisError(Exception):
    """Base exception for financial analysis errors"""

    def __init__(self, message: str, error_code: str, details: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()

        # Log the error
        logger.error(
            f"Error {error_code}: {message}",
            extra={
                "error_code": error_code,
                "details": details,
                "timestamp": self.timestamp,
            },
        )


class QuickBooksError(FinancialAnalysisError):
    """QuickBooks API related errors"""

    def __init__(self, message: str, qb_error_code: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            error_code=f"QB_{qb_error_code}" if qb_error_code else "QB_ERROR",
            details=kwargs,
        )


class DataProcessingError(FinancialAnalysisError):
    """Data processing and calculation errors"""

    def __init__(self, message: str, processing_stage: str, **kwargs):
        super().__init__(
            message=message,
            error_code=f"PROC_{processing_stage.upper()}",
            details=kwargs,
        )


def handle_financial_error(error: Exception) -> HTTPException:
    """Convert exceptions to appropriate HTTP responses"""
    if isinstance(error, FinancialAnalysisError):
        status_code = 400 if error.error_code.startswith("PROC_") else 500
        return HTTPException(
            status_code=status_code,
            detail={
                "error_code": error.error_code,
                "message": str(error),
                "details": error.details,
                "timestamp": error.timestamp.isoformat(),
            },
        )

    # Unexpected errors
    logger.error("Unexpected error", exc_info=error)
    return HTTPException(
        status_code=500,
        detail={
            "error_code": "UNEXPECTED_ERROR",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


def log_api_call(endpoint: str, realm_id: str, **kwargs):
    """Log API call details"""
    logger.info(
        f"API call to {endpoint}",
        extra={
            "endpoint": endpoint,
            "realm_id": realm_id,
            "parameters": kwargs,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


def log_performance(operation: str, start_time: datetime, **kwargs):
    """Log performance metrics"""
    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        f"Performance: {operation}",
        extra={
            "operation": operation,
            "duration_seconds": duration,
            "parameters": kwargs,
            "timestamp": start_time.isoformat(),
        },
    )
