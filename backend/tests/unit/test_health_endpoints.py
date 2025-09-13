"""
Unit tests for health check endpoints
"""
import os
import time
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.health import update_model_stats, get_model_stats, _model_stats


@pytest.fixture
def client():
    """FastAPI test client fixture"""
    return TestClient(app)


@pytest.fixture
def mock_system_info():
    """Mock system information for testing"""
    return {
        "cpu_percent": 25.5,
        "memory": {
            "total_mb": 8192.0,
            "available_mb": 4096.0,
            "used_mb": 4096.0,
            "percent": 50.0
        },
        "disk": {
            "total_gb": 500.0,
            "free_gb": 250.0,
            "used_gb": 250.0,
            "percent": 50.0
        },
        "load_average": [1.0, 1.5, 2.0]
    }


class TestHealthEndpoint:
    """Test cases for the health check endpoint"""
    
    def test_health_check_success(self, client, mock_system_info):
        """Test successful health check response"""
        with patch('app.api.health.get_system_info', return_value=mock_system_info):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert "status" in data
            assert "timestamp" in data
            assert "version" in data
            assert "environment" in data
            assert "uptime_seconds" in data
            assert "system" in data
            
            # Check values
            assert data["status"] == "healthy"
            assert data["version"] == "1.0.0"
            assert data["environment"] == "development"
            assert isinstance(data["uptime_seconds"], (int, float))
            assert data["uptime_seconds"] >= 0
            
            # Check system info
            assert data["system"]["cpu_percent"] == 25.5
            assert data["system"]["memory"]["percent"] == 50.0
    
    def test_health_check_degraded_high_memory(self, client):
        """Test health check with high memory usage (degraded status)"""
        degraded_system_info = {
            "cpu_percent": 25.0,
            "memory": {
                "total_mb": 8192.0,
                "available_mb": 819.2,
                "used_mb": 7372.8,
                "percent": 95.0  # High memory usage
            },
            "disk": {
                "total_gb": 500.0,
                "free_gb": 250.0,
                "used_gb": 250.0,
                "percent": 50.0
            }
        }
        
        with patch('app.api.health.get_system_info', return_value=degraded_system_info):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
    
    def test_health_check_degraded_high_cpu(self, client):
        """Test health check with high CPU usage (degraded status)"""
        degraded_system_info = {
            "cpu_percent": 95.0,  # High CPU usage
            "memory": {
                "total_mb": 8192.0,
                "available_mb": 4096.0,
                "used_mb": 4096.0,
                "percent": 50.0
            },
            "disk": {
                "total_gb": 500.0,
                "free_gb": 250.0,
                "used_gb": 250.0,
                "percent": 50.0
            }
        }
        
        with patch('app.api.health.get_system_info', return_value=degraded_system_info):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
    
    def test_health_check_system_error(self, client):
        """Test health check with system info error"""
        error_system_info = {"error": "Unable to retrieve system information"}
        
        with patch('app.api.health.get_system_info', return_value=error_system_info):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert "error" in data["system"]
    
    def test_health_check_exception_handling(self, client):
        """Test health check exception handling"""
        with patch('app.api.health.get_system_info', side_effect=Exception("System error")):
            response = client.get("/api/v1/health")
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "error" in data


class TestModelStatusEndpoint:
    """Test cases for the model status endpoint"""
    
    def setup_method(self):
        """Reset model stats before each test"""
        global _model_stats
        _model_stats.update({
            "total_predictions": 0,
            "last_prediction_time": None,
            "model_loaded": False,
            "error_message": None
        })
    
    def test_model_status_not_loaded(self, client):
        """Test model status when model is not loaded"""
        with patch('os.path.exists', return_value=False):
            response = client.get("/api/v1/models/status")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check response structure
            assert "status" in data
            assert "model_loaded" in data
            assert "model_path" in data
            assert "model_info" in data
            assert "last_prediction_time" in data
            assert "total_predictions" in data
            
            # Check values
            assert data["status"] == "not_loaded"
            assert data["model_loaded"] is False
            assert data["total_predictions"] == 0
            assert data["last_prediction_time"] is None
    
    def test_model_status_ready(self, client):
        """Test model status when model is loaded and ready"""
        # Set up model as loaded
        update_model_stats(loaded=True)
        
        mock_stat = MagicMock()
        mock_stat.st_size = 1024 * 1024 * 50  # 50MB
        mock_stat.st_mtime = time.time()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.stat', return_value=mock_stat):
            
            response = client.get("/api/v1/models/status")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "ready"
            assert data["model_loaded"] is True
            assert data["model_info"] is not None
            assert data["model_info"]["file_size_mb"] == 50.0
            assert "confidence_threshold" in data["model_info"]
    
    def test_model_status_with_predictions(self, client):
        """Test model status with prediction statistics"""
        # Set up model with some predictions
        update_model_stats(loaded=True)
        update_model_stats(prediction_made=True)
        update_model_stats(prediction_made=True)
        
        with patch('os.path.exists', return_value=True), \
             patch('os.stat', return_value=MagicMock(st_size=1024*1024, st_mtime=time.time())):
            
            response = client.get("/api/v1/models/status")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["total_predictions"] == 2
            assert data["last_prediction_time"] is not None
            assert isinstance(data["last_prediction_time"], (int, float))
    
    def test_model_status_with_error(self, client):
        """Test model status when there's an error"""
        error_message = "Model loading failed"
        update_model_stats(loaded=False, error=error_message)
        
        with patch('os.path.exists', return_value=True):
            response = client.get("/api/v1/models/status")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["status"] == "error"
            assert data["model_loaded"] is False
            assert data["error_message"] == error_message
    
    def test_model_status_exception_handling(self, client):
        """Test model status exception handling"""
        with patch('app.api.health.check_model_status', side_effect=Exception("Model check error")):
            response = client.get("/api/v1/models/status")
            
            assert response.status_code == 500
            data = response.json()
            assert data["success"] is False
            assert "error" in data


class TestModelStatsUtilities:
    """Test cases for model statistics utility functions"""
    
    def setup_method(self):
        """Reset model stats before each test"""
        global _model_stats
        _model_stats.update({
            "total_predictions": 0,
            "last_prediction_time": None,
            "model_loaded": False,
            "error_message": None
        })
    
    def test_update_model_stats_loaded(self):
        """Test updating model loaded status"""
        update_model_stats(loaded=True)
        stats = get_model_stats()
        assert stats["model_loaded"] is True
        
        update_model_stats(loaded=False)
        stats = get_model_stats()
        assert stats["model_loaded"] is False
    
    def test_update_model_stats_error(self):
        """Test updating model error message"""
        error_msg = "Test error message"
        update_model_stats(error=error_msg)
        stats = get_model_stats()
        assert stats["error_message"] == error_msg
    
    def test_update_model_stats_prediction(self):
        """Test updating prediction statistics"""
        initial_time = time.time()
        
        # Make first prediction
        update_model_stats(prediction_made=True)
        stats = get_model_stats()
        assert stats["total_predictions"] == 1
        assert stats["last_prediction_time"] >= initial_time
        
        # Make second prediction
        update_model_stats(prediction_made=True)
        stats = get_model_stats()
        assert stats["total_predictions"] == 2
    
    def test_get_model_stats_returns_copy(self):
        """Test that get_model_stats returns a copy, not reference"""
        update_model_stats(loaded=True)
        stats1 = get_model_stats()
        stats2 = get_model_stats()
        
        # Modify one copy
        stats1["model_loaded"] = False
        
        # Original should be unchanged
        assert stats2["model_loaded"] is True
        assert get_model_stats()["model_loaded"] is True


class TestSystemInfoFunction:
    """Test cases for system information gathering"""
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('os.getloadavg')
    def test_get_system_info_success(self, mock_loadavg, mock_disk, mock_memory, mock_cpu):
        """Test successful system info gathering"""
        from app.api.health import get_system_info
        
        # Mock psutil responses
        mock_cpu.return_value = 25.5
        
        mock_memory_obj = MagicMock()
        mock_memory_obj.total = 8 * 1024 * 1024 * 1024  # 8GB
        mock_memory_obj.available = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory_obj.used = 4 * 1024 * 1024 * 1024  # 4GB
        mock_memory_obj.percent = 50.0
        mock_memory.return_value = mock_memory_obj
        
        mock_disk_obj = MagicMock()
        mock_disk_obj.total = 500 * 1024 * 1024 * 1024  # 500GB
        mock_disk_obj.free = 250 * 1024 * 1024 * 1024  # 250GB
        mock_disk_obj.used = 250 * 1024 * 1024 * 1024  # 250GB
        mock_disk.return_value = mock_disk_obj
        
        mock_loadavg.return_value = [1.0, 1.5, 2.0]
        
        result = get_system_info()
        
        assert result["cpu_percent"] == 25.5
        assert result["memory"]["total_mb"] == 8192.0
        assert result["memory"]["percent"] == 50.0
        assert result["disk"]["total_gb"] == 500.0
        assert result["load_average"] == [1.0, 1.5, 2.0]
    
    @patch('psutil.cpu_percent', side_effect=Exception("CPU error"))
    def test_get_system_info_exception(self, mock_cpu):
        """Test system info gathering with exception"""
        from app.api.health import get_system_info
        
        result = get_system_info()
        assert "error" in result
        assert result["error"] == "Unable to retrieve system information"