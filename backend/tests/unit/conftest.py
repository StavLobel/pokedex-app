"""
Unit test specific fixtures
"""
import pytest
from faker import Faker

fake = Faker()


@pytest.fixture
def sample_error_message():
    """Generate a sample error message for testing"""
    return fake.sentence()


@pytest.fixture
def sample_error_code():
    """Generate a sample error code for testing"""
    return fake.word().upper() + "_ERROR"


@pytest.fixture
def random_file_size():
    """Generate a random file size for testing"""
    return fake.random_int(min=1024, max=10 * 1024 * 1024)


@pytest.fixture
def random_image_dimensions():
    """Generate random image dimensions for testing"""
    width = fake.random_int(min=32, max=2048)
    height = fake.random_int(min=32, max=2048)
    return (width, height)
