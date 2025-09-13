"""
Integration test specific fixtures
"""

import pytest
from faker import Faker

fake = Faker()


@pytest.fixture
def performance_test_timeout():
    """Timeout for performance tests in seconds"""
    return 10.0


@pytest.fixture
def large_image_dimensions():
    """Dimensions for large image testing"""
    return (2000, 2000)


@pytest.fixture
def test_image_quality():
    """JPEG quality for test images"""
    return fake.random_int(min=70, max=95)
