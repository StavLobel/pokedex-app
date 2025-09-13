"""
FastAPI main application entry point
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.api.health import router as health_router
from app.api.identify import router as identify_router
from app.core.config import get_settings
from app.core.logging import setup_logging


# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Pokemon Image Recognition API", version=app.version)
    yield
    # Shutdown
    logger.info("Shutting down Pokemon Image Recognition API")


app = FastAPI(
    title="Pokemon Image Recognition API",
    description="AI-powered Pokemon identification service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.environment != "production" else None,
    redoc_url="/api/redoc" if settings.environment != "production" else None,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all HTTP requests with timing information"""
    start_time = time.time()
    
    # Generate request ID for tracing
    request_id = f"req_{int(time.time() * 1000000)}"
    
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        request_id=request_id,
        user_agent=request.headers.get("user-agent"),
        client_ip=request.client.host if request.client else None,
    )
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            request_id=request_id,
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response
        
    except Exception as exc:
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            request_id=request_id,
            error=str(exc),
            process_time_ms=round(process_time * 1000, 2),
        )
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with structured error responses"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        request_id=request_id,
        method=request.method,
        url=str(request.url),
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
            },
            "timestamp": time.time(),
            "request_id": request_id,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unhandled errors"""
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        request_id=request_id,
        method=request.method,
        url=str(request.url),
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please try again later.",
            },
            "timestamp": time.time(),
            "request_id": request_id,
        }
    )


# Include routers
app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(identify_router, prefix="/api/v1", tags=["identification"])


@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    return {
        "message": "Pokemon Image Recognition API",
        "version": app.version,
        "docs_url": "/api/docs" if settings.environment != "production" else None,
    }