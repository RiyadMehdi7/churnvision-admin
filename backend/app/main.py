from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.db import get_db
from app.core.logging_config import setup_logging, get_logger
from app.middleware import LoggingMiddleware, ErrorHandlerMiddleware, RateLimiterMiddleware

# Initialize logging
setup_logging(log_level=settings.LOG_LEVEL, json_logs=settings.JSON_LOGS)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Internal control plane for ChurnVision Enterprise",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add middleware (order matters - first added = outermost)
app.add_middleware(ErrorHandlerMiddleware, debug=settings.DEBUG)
app.add_middleware(RateLimiterMiddleware, requests_per_minute=100)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

logger.info("ChurnVision Admin Platform started", extra={"version": "0.1.0"})


@app.get("/health")
def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "service": "admin-platform"}


@app.get("/health/detailed")
def detailed_health_check(db: Session = Depends(get_db)):
    """
    Comprehensive health check endpoint.
    Checks database connectivity and returns detailed status.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "admin-platform",
        "version": "0.1.0",
        "checks": {}
    }

    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["checks"]["database"] = {
            "status": "healthy",
            "latency_ms": None
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Add more health checks as needed
    health_status["checks"]["api"] = {"status": "healthy"}

    return health_status


@app.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes-style readiness probe.
    Returns 200 if the service is ready to accept traffic.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service not ready")


@app.get("/live")
def liveness_check():
    """
    Kubernetes-style liveness probe.
    Returns 200 if the service is alive.
    """
    return {"alive": True}
