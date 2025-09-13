"""
Health check and monitoring endpoints
"""
import os
import time
import psutil
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
router = APIRouter()
settings = get_settings()


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    timestamp: float
    version: str
    environment: str
    uptime_seconds: float
    system: Dict[str, Any]


class ModelStatusResponse(BaseModel):
    """AI model status response model"""
    status: str
    model_loaded: bool
    model_path: str
    model_info: Optional[Dict[str, Any]] = None
    last_prediction_time: Optional[float] = None
    total_predictions: int = 0
    error_message: Optional[str] = None


# Track application start time for uptime calculation
_start_time = time.time()
_model_stats = {
    "total_predictions": 0,
    "last_prediction_time": None,
    "model_loaded": False,
    "error_message": None
}


def get_system_info() -> Dict[str, Any]:
    """Get current system resource information"""
    try:
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        memory_info = {
            "total_mb": round(memory.total / 1024 / 1024, 2),
            "available_mb": round(memory.available / 1024 / 1024, 2),
            "used_mb": round(memory.used / 1024 / 1024, 2),
            "percent": memory.percent
        }
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_info = {
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
            "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
            "percent": round((disk.used / disk.total) * 100, 2)
        }
        
        return {
            "cpu_percent": cpu_percent,
            "memory": memory_info,
            "disk": disk_info,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }
    except Exception as e:
        logger.warning("Failed to get system info", error=str(e))
        return {"error": "Unable to retrieve system information"}


def check_model_status() -> Dict[str, Any]:
    """Check AI model availability and status"""
    try:
        model_path = settings.model_path
        model_exists = os.path.exists(model_path)
        
        # In a real implementation, this would check if the model is loaded in memory
        # For now, we'll simulate based on file existence
        model_loaded = model_exists and _model_stats["model_loaded"]
        
        model_info = None
        if model_exists:
            try:
                stat = os.stat(model_path)
                model_info = {
                    "file_size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "modified_time": stat.st_mtime,
                    "confidence_threshold": settings.model_confidence_threshold
                }
            except Exception as e:
                logger.warning("Failed to get model file info", error=str(e))
        
        return {
            "model_loaded": model_loaded,
            "model_path": model_path,
            "model_info": model_info,
            "last_prediction_time": _model_stats["last_prediction_time"],
            "total_predictions": _model_stats["total_predictions"],
            "error_message": _model_stats["error_message"]
        }
    except Exception as e:
        logger.error("Failed to check model status", error=str(e))
        return {
            "model_loaded": False,
            "model_path": settings.model_path,
            "model_info": None,
            "last_prediction_time": None,
            "total_predictions": 0,
            "error_message": f"Model status check failed: {str(e)}"
        }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint that returns system status and basic metrics.
    
    Returns:
        HealthResponse: System health information including uptime, 
                       resource usage, and service status
    """
    try:
        current_time = time.time()
        uptime = current_time - _start_time
        
        system_info = get_system_info()
        
        # Determine overall health status
        status = "healthy"
        if "error" in system_info:
            status = "degraded"
        elif system_info.get("memory", {}).get("percent", 0) > 90:
            status = "degraded"
        elif system_info.get("cpu_percent", 0) > 90:
            status = "degraded"
        
        logger.info(
            "Health check performed",
            status=status,
            uptime_seconds=uptime,
            cpu_percent=system_info.get("cpu_percent"),
            memory_percent=system_info.get("memory", {}).get("percent")
        )
        
        return HealthResponse(
            status=status,
            timestamp=current_time,
            version="1.0.0",
            environment=settings.environment,
            uptime_seconds=round(uptime, 2),
            system=system_info
        )
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Health check failed"
        )


@router.get("/models/status", response_model=ModelStatusResponse)
async def model_status():
    """
    AI model status endpoint for monitoring model availability and performance.
    
    Returns:
        ModelStatusResponse: AI model status including load state,
                           performance metrics, and error information
    """
    try:
        model_status_info = check_model_status()
        
        # Determine model status
        if model_status_info["model_loaded"]:
            status = "ready"
        elif model_status_info["error_message"]:
            status = "error"
        else:
            status = "not_loaded"
        
        logger.info(
            "Model status check performed",
            status=status,
            model_loaded=model_status_info["model_loaded"],
            total_predictions=model_status_info["total_predictions"]
        )
        
        return ModelStatusResponse(
            status=status,
            **model_status_info
        )
        
    except Exception as e:
        logger.error("Model status check failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Model status check failed"
        )


# Utility functions for updating model stats (to be used by AI service)
def update_model_stats(loaded: bool = None, error: str = None, prediction_made: bool = False):
    """Update model statistics (called by AI service)"""
    global _model_stats
    
    if loaded is not None:
        _model_stats["model_loaded"] = loaded
    
    if error is not None:
        _model_stats["error_message"] = error
    
    if prediction_made:
        _model_stats["total_predictions"] += 1
        _model_stats["last_prediction_time"] = time.time()


def get_model_stats() -> Dict[str, Any]:
    """Get current model statistics"""
    return _model_stats.copy()