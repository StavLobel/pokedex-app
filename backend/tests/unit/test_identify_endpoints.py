"""
Unit tests for identify API endpoints
"""
import io
import pytest
from unittest.mock import patch
from PIL import Image
from faker import Faker

from app.services.image_validation import ImageValidationError

fake = Faker()


class TestIdentifyPokemonEndpoint:
    """Test the /api/v1/identify endpoint"""
    
    def test_identify_pokemon_success(self, client, valid_image_file_data):
        """Test successful image upload and preprocessing"""
        filename, file_content, content_type = valid_image_file_data
        
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, file_content, content_type)}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert data["success"] is True
        assert data["data"] is not None
        assert data["error"] is None
        assert "processing_time_ms" in data
        assert "timestamp" in data
        assert "request_id" in data
        
        # Check that preprocessing was successful
        assert "upload_stats" in data["data"]
        assert "preprocessing" in data["data"]
        
        upload_stats = data["data"]["upload_stats"]
        assert upload_stats["filename"] == filename
        assert upload_stats["content_type"] == content_type
        assert upload_stats["size_bytes"] > 0
        assert "image_hash" in upload_stats
        assert "dimensions" in upload_stats
    
    def test_identify_pokemon_no_file(self, client):
        """Test endpoint without uploading a file"""
        response = client.post("/api/v1/identify")
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_identify_pokemon_invalid_file_type(self, client, invalid_file_data):
        """Test endpoint with invalid file type"""
        filename, file_content, content_type = invalid_file_data
        
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, file_content, content_type)}
        )
        
        assert response.status_code == 200  # We return 200 with error in body
        data = response.json()
        
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"] is not None
        assert data["error"]["code"] == "INVALID_FILE_TYPE"
        assert "not supported" in data["error"]["message"]
    
    def test_identify_pokemon_corrupted_image(self, client):
        """Test endpoint with corrupted image data"""
        # Create a file that claims to be JPEG but has invalid content
        corrupted_content = fake.text(max_nb_chars=100).encode('utf-8')
        filename = fake.file_name(extension='jpg')
        
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, io.BytesIO(corrupted_content), "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_IMAGE_FORMAT"
    
    @patch('app.services.image_validation.image_validation_service.validate_file')
    def test_identify_pokemon_validation_error(self, mock_validate, client, valid_image_file_data):
        """Test endpoint when validation service raises error"""
        filename, file_content, content_type = valid_image_file_data
        
        # Mock validation to raise an error
        error_message = fake.sentence()
        mock_validate.side_effect = ImageValidationError(error_message, "FILE_TOO_LARGE")
        
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, file_content, content_type)}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "FILE_TOO_LARGE"
        assert error_message in data["error"]["message"]
    
    @patch('app.services.image_validation.image_validation_service.read_and_validate_image')
    def test_identify_pokemon_unexpected_error(self, mock_read, client, valid_image_file_data):
        """Test endpoint when unexpected error occurs"""
        filename, file_content, content_type = valid_image_file_data
        
        # Mock to raise unexpected error
        error_message = fake.sentence()
        mock_read.side_effect = Exception(error_message)
        
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, file_content, content_type)}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "unexpected error occurred" in data["error"]["message"]
    
    def test_identify_pokemon_png_file(self, client):
        """Test endpoint with PNG file"""
        img = Image.new('RGB', (150, 150), color=fake.color())
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        filename = fake.file_name(extension='png')
        
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, img_bytes, "image/png")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["upload_stats"]["content_type"] == "image/png"
    
    def test_identify_pokemon_webp_file(self, client):
        """Test endpoint with WebP file"""
        img = Image.new('RGB', (120, 120), color=fake.color())
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='WebP')
        img_bytes.seek(0)
        filename = fake.file_name(extension='webp')
        
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, img_bytes, "image/webp")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["upload_stats"]["content_type"] == "image/webp"


class TestUploadInfoEndpoint:
    """Test the /api/v1/identify/info endpoint"""
    
    def test_get_upload_info(self, client):
        """Test getting upload information"""
        response = client.get("/api/v1/identify/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "supported_formats" in data
        assert "max_file_size_bytes" in data
        assert "max_file_size_formatted" in data
        assert "target_image_size" in data
        assert "minimum_image_size" in data
        assert "preprocessing" in data
        
        # Check supported formats
        supported_formats = data["supported_formats"]
        assert "image/jpeg" in supported_formats
        assert "image/png" in supported_formats
        assert "image/webp" in supported_formats
        
        # Check file size information
        assert isinstance(data["max_file_size_bytes"], int)
        assert data["max_file_size_bytes"] > 0
        assert "MB" in data["max_file_size_formatted"]
        
        # Check preprocessing information
        preprocessing = data["preprocessing"]
        assert "format_conversion" in preprocessing
        assert "resizing" in preprocessing
        assert "normalization" in preprocessing


class TestErrorResponseFormat:
    """Test error response format consistency"""
    
    def test_validation_error_response_format(self, client):
        """Test that validation errors follow consistent format"""
        # Upload a GIF file (unsupported format)
        img = Image.new('RGB', (50, 50), color=fake.color())
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='GIF')
        img_bytes.seek(0)
        filename = fake.file_name(extension='gif')
        
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, img_bytes, "image/gif")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check error response structure
        assert data["success"] is False
        assert data["data"] is None
        assert data["error"] is not None
        
        error = data["error"]
        assert "code" in error
        assert "message" in error
        assert "supported_formats" in error
        assert "max_file_size" in error
        
        # Check metadata
        assert "processing_time_ms" in data
        assert "timestamp" in data
        assert "request_id" in data
        assert isinstance(data["processing_time_ms"], (int, float))
        assert isinstance(data["timestamp"], (int, float))
        assert isinstance(data["request_id"], str)


class TestRequestIdGeneration:
    """Test request ID generation and tracking"""
    
    def test_request_id_uniqueness(self, client, valid_image_file_data):
        """Test that each request gets a unique request ID"""
        filename, file_content, content_type = valid_image_file_data
        
        # Make two identical requests
        response1 = client.post(
            "/api/v1/identify",
            files={"image": (filename, file_content, content_type)}
        )
        
        # Reset file pointer for second request
        file_content.seek(0)
        response2 = client.post(
            "/api/v1/identify",
            files={"image": (filename, file_content, content_type)}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # Request IDs should be different
        assert data1["request_id"] != data2["request_id"]
        
        # Both should start with "req_"
        assert data1["request_id"].startswith("req_")
        assert data2["request_id"].startswith("req_")


class TestPerformanceMetrics:
    """Test performance metrics in responses"""
    
    def test_processing_time_measurement(self, client, valid_image_file_data):
        """Test that processing time is measured and reported"""
        filename, file_content, content_type = valid_image_file_data
        
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, file_content, content_type)}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Processing time should be present and reasonable
        processing_time = data["processing_time_ms"]
        assert isinstance(processing_time, (int, float))
        assert processing_time > 0
        assert processing_time < 10000  # Should be less than 10 seconds for test image
    
    def test_timestamp_accuracy(self, client, valid_image_file_data):
        """Test that timestamp is accurate"""
        import time
        
        filename, file_content, content_type = valid_image_file_data
        
        before_request = time.time()
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, file_content, content_type)}
        )
        after_request = time.time()
        
        assert response.status_code == 200
        data = response.json()
        
        timestamp = data["timestamp"]
        assert before_request <= timestamp <= after_request