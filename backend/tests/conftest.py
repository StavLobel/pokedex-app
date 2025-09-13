"""
Global test configuration and fixtures
"""

import io
from unittest.mock import AsyncMock, Mock

import pytest
from faker import Faker
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.image_validation import ImageValidationService

# Initialize faker
fake = Faker()


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def image_validation_service():
    """Create ImageValidationService instance for testing"""
    return ImageValidationService()


@pytest.fixture
def valid_jpeg_file():
    """Create a valid JPEG UploadFile mock for testing"""
    # Create a simple test image
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    # Create mock file with proper attributes
    file = Mock()
    file.filename = fake.file_name(extension="jpg")
    file.content_type = "image/jpeg"
    file.size = len(img_bytes.getvalue())
    file.read = AsyncMock(return_value=img_bytes.getvalue())
    return file


@pytest.fixture
def valid_png_file():
    """Create a valid PNG UploadFile mock for testing"""
    img = Image.new("RGB", (200, 200), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # Create mock file with proper attributes
    file = Mock()
    file.filename = fake.file_name(extension="png")
    file.content_type = "image/png"
    file.size = len(img_bytes.getvalue())
    file.read = AsyncMock(return_value=img_bytes.getvalue())
    return file


@pytest.fixture
def valid_webp_file():
    """Create a valid WebP UploadFile mock for testing"""
    img = Image.new("RGB", (150, 150), color="purple")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="WebP")
    img_bytes.seek(0)

    # Create mock file with proper attributes
    file = Mock()
    file.filename = fake.file_name(extension="webp")
    file.content_type = "image/webp"
    file.size = len(img_bytes.getvalue())
    file.read = AsyncMock(return_value=img_bytes.getvalue())
    return file


@pytest.fixture
def large_file():
    """Create a file that exceeds size limit"""
    file = Mock()
    file.filename = fake.file_name(extension="jpg")
    file.content_type = "image/jpeg"
    file.size = 15 * 1024 * 1024  # 15MB (exceeds 10MB limit)
    return file


@pytest.fixture
def invalid_type_file():
    """Create a file with invalid MIME type"""
    file = Mock()
    file.filename = fake.file_name(extension="gif")
    file.content_type = "image/gif"
    file.size = fake.random_int(min=1024, max=5000)
    return file


@pytest.fixture
def no_filename_file():
    """Create a file with no filename"""
    file = Mock()
    file.filename = None
    file.content_type = "image/jpeg"
    file.size = fake.random_int(min=1024, max=5000)
    return file


@pytest.fixture
def corrupted_image_file():
    """Create a file with corrupted image data"""
    corrupted_data = fake.text(max_nb_chars=200).encode("utf-8")
    file = Mock()
    file.filename = fake.file_name(extension="jpg")
    file.content_type = "image/jpeg"
    file.size = len(corrupted_data)
    file.read = AsyncMock(return_value=corrupted_data)
    return file


@pytest.fixture
def tiny_image_file():
    """Create a very small image file (below minimum size)"""
    # Create a very small image (16x16)
    img = Image.new("RGB", (16, 16), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)

    file = Mock()
    file.filename = fake.file_name(extension="jpg")
    file.content_type = "image/jpeg"
    file.size = len(img_bytes.getvalue())
    file.read = AsyncMock(return_value=img_bytes.getvalue())
    return file


# Test data fixtures for API testing
@pytest.fixture
def valid_image_file_data():
    """Create a valid image file data tuple for API testing"""
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    filename = fake.file_name(extension="jpg")
    return (filename, img_bytes, "image/jpeg")


@pytest.fixture
def large_image_file_data():
    """Create a large image file data tuple for API testing"""
    # Create a large image
    img = Image.new("RGB", (2000, 2000), color="blue")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG", quality=100)
    img_bytes.seek(0)
    filename = fake.file_name(extension="jpg")
    return (filename, img_bytes, "image/jpeg")


@pytest.fixture
def invalid_file_data():
    """Create an invalid file data tuple for API testing"""
    content = fake.text(max_nb_chars=100).encode("utf-8")
    filename = fake.file_name(extension="txt")
    return (filename, io.BytesIO(content), "text/plain")


# PIL Image fixtures for preprocessing tests
@pytest.fixture
def rgb_image():
    """Create an RGB PIL Image for testing"""
    return Image.new("RGB", (300, 400), color=fake.color())


@pytest.fixture
def rgba_image():
    """Create an RGBA PIL Image for testing"""
    color = tuple(fake.random_int(0, 255) for _ in range(4))
    return Image.new("RGBA", (200, 200), color=color)


@pytest.fixture
def grayscale_image():
    """Create a grayscale PIL Image for testing"""
    return Image.new("L", (150, 150), color=fake.random_int(0, 255))


@pytest.fixture
def wide_image():
    """Create a wide aspect ratio PIL Image for testing"""
    return Image.new("RGB", (400, 200), color=fake.color())


@pytest.fixture
def tall_image():
    """Create a tall aspect ratio PIL Image for testing"""
    return Image.new("RGB", (200, 400), color=fake.color())


@pytest.fixture
def square_image():
    """Create a square PIL Image for testing"""
    return Image.new("RGB", (300, 300), color=fake.color())


# Utility fixtures
@pytest.fixture
def random_bytes():
    """Generate random bytes for testing"""
    return fake.binary(length=fake.random_int(min=100, max=1000))


@pytest.fixture
def fake_hash():
    """Generate a fake SHA-256 hash for testing"""
    return fake.sha256()


@pytest.fixture
def fake_request_id():
    """Generate a fake request ID for testing"""
    return f"req_{fake.random_int(min=1000000000000, max=9999999999999)}"
