"""
Integration tests for complete image upload and validation flow
"""

import io

import pytest
from faker import Faker
from PIL import Image

fake = Faker()


class TestImageUploadIntegration:
    """Integration tests for image upload functionality"""

    def test_complete_image_upload_flow_jpeg(self, client):
        """Test complete flow with JPEG image"""
        # Create a test JPEG image
        img = Image.new("RGB", (300, 200), color=fake.color())
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG", quality=85)
        img_bytes.seek(0)
        filename = fake.file_name(extension="jpg")

        # Upload the image
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, img_bytes.getvalue(), "image/jpeg")},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["data"] is not None
        assert data["error"] is None

        # Verify upload stats
        upload_stats = data["data"]["upload_stats"]
        assert upload_stats["filename"] == filename
        assert upload_stats["content_type"] == "image/jpeg"
        assert upload_stats["dimensions"] == "300x200"
        assert upload_stats["format"] == "JPEG"
        assert len(upload_stats["image_hash"]) == 64

        # Verify preprocessing
        preprocessing = data["data"]["preprocessing"]
        assert preprocessing["target_size"] == "224x224"
        assert preprocessing["format"] == "RGB"
        assert preprocessing["normalized"] is True
        assert preprocessing["shape"] == [1, 3, 224, 224]

    def test_complete_image_upload_flow_png(self, client):
        """Test complete flow with PNG image"""
        # Create a test PNG image
        color = tuple(fake.random_int(0, 255) for _ in range(4))
        img = Image.new("RGBA", (150, 150), color=color)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        filename = fake.file_name(extension="png")

        # Upload the image
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, img_bytes.getvalue(), "image/png")},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        upload_stats = data["data"]["upload_stats"]
        assert upload_stats["content_type"] == "image/png"
        assert upload_stats["format"] == "PNG"

    def test_complete_image_upload_flow_webp(self, client):
        """Test complete flow with WebP image"""
        # Create a test WebP image
        img = Image.new("RGB", (400, 300), color=fake.color())
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="WebP", quality=80)
        img_bytes.seek(0)
        filename = fake.file_name(extension="webp")

        # Upload the image
        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, img_bytes.getvalue(), "image/webp")},
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        upload_stats = data["data"]["upload_stats"]
        assert upload_stats["content_type"] == "image/webp"
        assert upload_stats["format"] == "WEBP"

    def test_error_handling_invalid_format(self, client):
        """Test error handling for invalid file format"""
        # Create a text file disguised as an image
        text_content = fake.text(max_nb_chars=100).encode("utf-8")
        filename = fake.file_name(extension="jpg")

        response = client.post(
            "/api/v1/identify", files={"image": (filename, text_content, "image/jpeg")}
        )

        # Verify error response
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert data["data"] is None
        assert data["error"] is not None
        assert data["error"]["code"] == "INVALID_IMAGE_FORMAT"

    def test_error_handling_unsupported_type(self, client):
        """Test error handling for unsupported file type"""
        # Create a GIF image (not supported)
        img = Image.new("RGB", (100, 100), color=fake.color())
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="GIF")
        img_bytes.seek(0)
        filename = fake.file_name(extension="gif")

        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, img_bytes.getvalue(), "image/gif")},
        )

        # Verify error response
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_FILE_TYPE"
        assert "image/gif" in data["error"]["message"]

    def test_performance_requirements(self, client):
        """Test that processing meets performance requirements"""
        # Create a reasonably sized image
        img = Image.new("RGB", (800, 600), color=fake.color())
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG", quality=90)
        img_bytes.seek(0)
        filename = fake.file_name(extension="jpg")

        response = client.post(
            "/api/v1/identify",
            files={"image": (filename, img_bytes.getvalue(), "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify processing time is reasonable (should be well under 10 seconds for preprocessing)
        processing_time = data["processing_time_ms"]
        assert processing_time < 5000  # Less than 5 seconds for preprocessing

        # Verify response structure
        assert data["success"] is True
        assert "request_id" in data
        assert "timestamp" in data

    def test_info_endpoint_consistency(self, client):
        """Test that info endpoint provides accurate information"""
        response = client.get("/api/v1/identify/info")

        assert response.status_code == 200
        info = response.json()

        # Verify required fields
        assert "supported_formats" in info
        assert "max_file_size_bytes" in info
        assert "target_image_size" in info

        # Verify supported formats match what we test
        supported_formats = info["supported_formats"]
        assert "image/jpeg" in supported_formats
        assert "image/png" in supported_formats
        assert "image/webp" in supported_formats

        # Verify max file size is reasonable
        max_size = info["max_file_size_bytes"]
        assert max_size == 10 * 1024 * 1024  # 10MB

    def test_request_id_tracking(self, client):
        """Test that request IDs are properly generated and tracked"""
        img = Image.new("RGB", (100, 100), color=fake.color())
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        # Make multiple requests
        responses = []
        for i in range(3):
            img_bytes.seek(0)
            filename = fake.file_name(extension="jpg")
            response = client.post(
                "/api/v1/identify",
                files={"image": (filename, img_bytes.getvalue(), "image/jpeg")},
            )
            responses.append(response.json())

        # Verify all requests have unique IDs
        request_ids = [r["request_id"] for r in responses]
        assert len(set(request_ids)) == 3  # All unique

        # Verify all IDs follow expected format
        for req_id in request_ids:
            assert req_id.startswith("req_")
            assert len(req_id) > 10  # Should be reasonably long
