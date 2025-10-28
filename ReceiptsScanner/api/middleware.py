"""
API Middleware - CORS, logging, and metrics tracking
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import os
from monitoring.logging_config import get_logger
from monitoring.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress
)

logger = get_logger(__name__)

def setup_middleware(app: FastAPI):
    """Setup all middleware for the FastAPI application"""
    
    # CORS Middleware
    cors_enabled = os.getenv("CORS_ENABLED", "true").lower() == "true"
    
    if cors_enabled:
        allowed_origins = os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:8501,http://localhost:3000"
        ).split(",")
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(f"CORS enabled for origins: {allowed_origins}")
    
    # Request logging and metrics middleware
    @app.middleware("http")
    async def log_and_metrics_middleware(request: Request, call_next):
        """Log requests and track metrics"""
        start_time = time.time()
        
        # Track in-progress requests
        http_requests_in_progress.labels(
            method=request.method,
            endpoint=request.url.path
        ).inc()
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            status_code = 500
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Track metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=request.url.path,
                status=str(status_code)
            ).inc()
            
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            http_requests_in_progress.labels(
                method=request.method,
                endpoint=request.url.path
            ).dec()
            
            # Log request
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration=duration
            )
        
        return response
    
    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler"""
        logger.error(
            "unhandled_exception",
            error=str(exc),
            path=request.url.path,
            method=request.method
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred",
                "path": request.url.path
            }
        )
    
    logger.info("Middleware setup completed")