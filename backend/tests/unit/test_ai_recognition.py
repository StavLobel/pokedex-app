"""
Unit tests for AI recognition service and mock classifier.
"""
import asyncio
import io
from unittest.mock import Mock, patch

import numpy as np
import pytest
from PIL import Image

from app.models.ai import (BoundingBox, ImageProcessingConfig,
                           ImageProcessingError, ModelInfo,
                           ModelNotLoadedError, ModelType,
                           PokemonIdentification, Prediction, PredictionError)
from app.services.ai_recognition import (ImageRecognitionService,
                                         MockPokemonClassifier,
                                         get_recognition_service)


class TestImageProcessingConfig:
    """Test image processing configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ImageProcessingConfig()

        assert config.target_size == (224, 224)
        assert config.normalize_mean == [0.485, 0.456, 0.406]
        assert config.normalize_std == [0.229, 0.224, 0.225]
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.supported_formats == ["JPEG", "PNG", "WebP"]

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ImageProcessingConfig(
            target_size=(256, 256),
            max_file_size=5 * 1024 * 1024,
            supported_formats=["JPEG", "PNG"],
        )

        assert config.target_size == (256, 256)
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.supported_formats == ["JPEG", "PNG"]


class TestPrediction:
    """Test Prediction model."""

    def test_valid_prediction(self):
        """Test creating a valid prediction."""
        prediction = Prediction(pokemon_name="pikachu", pokemon_id=25, confidence=0.85)

        assert prediction.pokemon_name == "pikachu"
        assert prediction.pokemon_id == 25
        assert prediction.confidence == 0.85
        assert prediction.confidence_level.value == "high"

    def test_prediction_confidence_levels(self):
        """Test confidence level categorization."""
        high_pred = Prediction(pokemon_name="pikachu", pokemon_id=25, confidence=0.8)
        medium_pred = Prediction(pokemon_name="bulbasaur", pokemon_id=1, confidence=0.5)
        low_pred = Prediction(pokemon_name="charmander", pokemon_id=4, confidence=0.2)

        assert high_pred.confidence_level.value == "high"
        assert medium_pred.confidence_level.value == "medium"
        assert low_pred.confidence_level.value == "low"

    def test_prediction_validation(self):
        """Test prediction validation."""
        # Test empty name
        with pytest.raises(ValueError, match="Pokemon name cannot be empty"):
            Prediction(pokemon_name="", pokemon_id=25, confidence=0.8)

        # Test invalid ID
        with pytest.raises(ValueError):
            Prediction(pokemon_name="pikachu", pokemon_id=0, confidence=0.8)

        # Test name normalization
        prediction = Prediction(
            pokemon_name="  PIKACHU  ", pokemon_id=25, confidence=0.8
        )
        assert prediction.pokemon_name == "pikachu"


class TestPokemonIdentification:
    """Test PokemonIdentification model."""

    def test_high_confidence_identification(self):
        """Test identification with high confidence."""
        primary = Prediction(pokemon_name="pikachu", pokemon_id=25, confidence=0.9)
        identification = PokemonIdentification(
            primary_prediction=primary,
            processing_time_ms=150,
            model_version="mock-v1.0.0",
        )

        assert identification.has_high_confidence is True
        assert identification.needs_user_selection is False
        assert len(identification.alternative_predictions) == 0

    def test_low_confidence_identification(self):
        """Test identification with low confidence and alternatives."""
        primary = Prediction(pokemon_name="pikachu", pokemon_id=25, confidence=0.5)
        alt1 = Prediction(pokemon_name="raichu", pokemon_id=26, confidence=0.4)
        alt2 = Prediction(pokemon_name="pichu", pokemon_id=172, confidence=0.3)

        identification = PokemonIdentification(
            primary_prediction=primary,
            alternative_predictions=[alt2, alt1],  # Test sorting
            processing_time_ms=200,
            model_version="mock-v1.0.0",
        )

        assert identification.has_high_confidence is False
        assert identification.needs_user_selection is True
        assert len(identification.alternative_predictions) == 2
        # Check that alternatives are sorted by confidence
        assert (
            identification.alternative_predictions[0].confidence
            >= identification.alternative_predictions[1].confidence
        )


class TestMockPokemonClassifier:
    """Test MockPokemonClassifier implementation."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ImageProcessingConfig()

    @pytest.fixture
    def classifier(self, config):
        """Create mock classifier instance."""
        return MockPokemonClassifier(config)

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes for testing."""
        # Create a simple RGB image
        image = Image.new("RGB", (100, 100), color="red")
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="JPEG")
        return img_bytes.getvalue()

    def test_classifier_initialization(self, classifier):
        """Test classifier initialization."""
        assert classifier.confidence_threshold == 0.7
        assert classifier.is_loaded is False
        assert classifier.model_version == "mock-v1.0.0"

    @pytest.mark.asyncio
    async def test_model_loading(self, classifier):
        """Test model loading."""
        assert classifier.is_loaded is False

        await classifier.load_model()

        assert classifier.is_loaded is True

    @pytest.mark.asyncio
    async def test_image_preprocessing(self, classifier, sample_image_bytes):
        """Test image preprocessing pipeline."""
        processed = await classifier.preprocess_image(sample_image_bytes)

        # Check output shape: (batch_size, height, width, channels)
        assert processed.shape == (1, 224, 224, 3)
        assert processed.dtype == np.float32

        # Check normalization (values should be roughly in [-2, 2] range after ImageNet normalization)
        assert processed.min() >= -3.0
        assert processed.max() <= 3.0

    @pytest.mark.asyncio
    async def test_image_preprocessing_different_formats(self, classifier):
        """Test preprocessing with different image formats."""
        # Test PNG
        png_image = Image.new("RGB", (50, 50), color="blue")
        png_bytes = io.BytesIO()
        png_image.save(png_bytes, format="PNG")

        processed_png = await classifier.preprocess_image(png_bytes.getvalue())
        assert processed_png.shape == (1, 224, 224, 3)

        # Test RGBA to RGB conversion
        rgba_image = Image.new("RGBA", (50, 50), color=(255, 0, 0, 128))
        rgba_bytes = io.BytesIO()
        rgba_image.save(rgba_bytes, format="PNG")

        processed_rgba = await classifier.preprocess_image(rgba_bytes.getvalue())
        assert processed_rgba.shape == (1, 224, 224, 3)

    @pytest.mark.asyncio
    async def test_image_preprocessing_invalid_data(self, classifier):
        """Test preprocessing with invalid image data."""
        with pytest.raises(ImageProcessingError):
            await classifier.preprocess_image(b"invalid image data")

    @pytest.mark.asyncio
    async def test_prediction_without_loading(self, classifier):
        """Test prediction fails when model is not loaded."""
        dummy_image = np.zeros((1, 224, 224, 3))

        with pytest.raises(ModelNotLoadedError):
            await classifier.predict(dummy_image)

    @pytest.mark.asyncio
    async def test_prediction_with_loaded_model(self, classifier):
        """Test prediction with loaded model."""
        await classifier.load_model()
        dummy_image = (
            np.ones((1, 224, 224, 3)) * 0.5
        )  # Consistent input for deterministic results

        predictions = await classifier.predict(dummy_image)

        assert len(predictions) >= 1
        assert isinstance(predictions[0], Prediction)
        assert predictions[0].confidence >= 0.0
        assert predictions[0].confidence <= 1.0
        assert predictions[0].pokemon_id > 0
        assert predictions[0].pokemon_name in [
            p["name"] for p in MockPokemonClassifier.MOCK_POKEMON_DATA
        ]

        # Check that predictions are sorted by confidence
        for i in range(len(predictions) - 1):
            assert predictions[i].confidence >= predictions[i + 1].confidence

    @pytest.mark.asyncio
    async def test_prediction_consistency(self, classifier):
        """Test that same image produces consistent predictions."""
        await classifier.load_model()
        dummy_image = np.ones((1, 224, 224, 3)) * 0.3

        predictions1 = await classifier.predict(dummy_image)
        predictions2 = await classifier.predict(dummy_image)

        # Should get same primary prediction for same image
        assert predictions1[0].pokemon_name == predictions2[0].pokemon_name
        assert predictions1[0].confidence == predictions2[0].confidence

    def test_model_info(self, classifier):
        """Test model information retrieval."""
        info = classifier.get_model_info()

        assert isinstance(info, ModelInfo)
        assert info.name == "Mock Pokemon Classifier"
        assert info.version == "mock-v1.0.0"
        assert info.type == ModelType.MOCK
        assert info.accuracy == 0.85
        assert info.input_shape == (224, 224, 3)
        assert info.num_classes == len(MockPokemonClassifier.MOCK_POKEMON_DATA)
        assert info.confidence_threshold == 0.7


class TestImageRecognitionService:
    """Test ImageRecognitionService."""

    @pytest.fixture
    def service(self):
        """Create recognition service instance."""
        return ImageRecognitionService()

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes for testing."""
        image = Image.new("RGB", (200, 200), color="green")
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="JPEG")
        return img_bytes.getvalue()

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service.classifier is not None
        assert isinstance(service.classifier, MockPokemonClassifier)
        assert service.config is not None

    @pytest.mark.asyncio
    async def test_service_initialize(self, service):
        """Test service initialization."""
        await service.initialize()
        assert service.classifier.is_loaded is True

    @pytest.mark.asyncio
    async def test_identify_pokemon_success(self, service, sample_image_bytes):
        """Test successful Pokemon identification."""
        await service.initialize()

        result = await service.identify_pokemon(sample_image_bytes)

        assert isinstance(result, PokemonIdentification)
        assert result.primary_prediction is not None
        assert result.processing_time_ms > 0
        assert result.model_version == "mock-v1.0.0"
        assert result.image_hash is not None
        assert len(result.image_hash) == 64  # SHA256 hash length

    @pytest.mark.asyncio
    async def test_identify_pokemon_without_initialization(
        self, service, sample_image_bytes
    ):
        """Test identification automatically initializes service."""
        # Don't call initialize manually
        result = await service.identify_pokemon(sample_image_bytes)

        assert isinstance(result, PokemonIdentification)
        assert service.classifier.is_loaded is True

    @pytest.mark.asyncio
    async def test_get_model_status(self, service):
        """Test model status retrieval."""
        # Before initialization
        status = await service.get_model_status()
        assert status["status"] == "not_loaded"
        assert status["is_loaded"] is False

        # After initialization
        await service.initialize()
        status = await service.get_model_status()
        assert status["status"] == "ready"
        assert status["is_loaded"] is True
        assert "model_info" in status
        assert "config" in status

    @pytest.mark.asyncio
    async def test_validate_image_success(self, service, sample_image_bytes):
        """Test successful image validation."""
        is_valid, error = await service.validate_image(sample_image_bytes)

        assert is_valid is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_image_too_large(self, service):
        """Test validation fails for oversized images."""
        # Create a large byte array that exceeds the limit (10MB)
        # Instead of creating a huge image, create a large fake byte array
        large_bytes = b"fake_image_data" * (1024 * 1024)  # ~15MB of fake data

        is_valid, error = await service.validate_image(large_bytes)

        assert is_valid is False
        assert "too large" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_image_too_small(self, service):
        """Test validation fails for tiny images."""
        tiny_image = Image.new("RGB", (10, 10), color="blue")
        img_bytes = io.BytesIO()
        tiny_image.save(img_bytes, format="JPEG")

        is_valid, error = await service.validate_image(img_bytes.getvalue())

        assert is_valid is False
        assert "too small" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_image_invalid_data(self, service):
        """Test validation fails for invalid image data."""
        is_valid, error = await service.validate_image(b"not an image")

        assert is_valid is False
        assert "invalid image" in error.lower()


class TestGlobalServiceInstance:
    """Test global service instance management."""

    @pytest.mark.asyncio
    async def test_get_recognition_service_singleton(self):
        """Test that get_recognition_service returns singleton instance."""
        # Clear any existing instance
        import app.services.ai_recognition as ai_module

        ai_module._recognition_service = None

        service1 = await get_recognition_service()
        service2 = await get_recognition_service()

        assert service1 is service2
        assert service1.classifier.is_loaded is True

    @pytest.mark.asyncio
    async def test_get_recognition_service_initialization(self):
        """Test that service is properly initialized on first call."""
        # Clear any existing instance
        import app.services.ai_recognition as ai_module

        ai_module._recognition_service = None

        service = await get_recognition_service()

        assert service is not None
        assert service.classifier is not None
        assert service.classifier.is_loaded is True


class TestBoundingBox:
    """Test BoundingBox model."""

    def test_valid_bounding_box(self):
        """Test creating valid bounding box."""
        bbox = BoundingBox(x=0.1, y=0.2, width=0.5, height=0.6)

        assert bbox.x == 0.1
        assert bbox.y == 0.2
        assert bbox.width == 0.5
        assert bbox.height == 0.6

    def test_bounding_box_validation(self):
        """Test bounding box validation."""
        # Test negative values
        with pytest.raises(ValueError):
            BoundingBox(x=-0.1, y=0.2, width=0.5, height=0.6)

        # Test values > 1
        with pytest.raises(ValueError):
            BoundingBox(x=0.1, y=0.2, width=1.5, height=0.6)


@pytest.mark.asyncio
async def test_integration_full_pipeline():
    """Integration test for the complete recognition pipeline."""
    # Create test image
    test_image = Image.new("RGB", (300, 300), color="yellow")
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format="JPEG")
    image_data = img_bytes.getvalue()

    # Get service and run full pipeline
    service = await get_recognition_service()

    # Validate image
    is_valid, error = await service.validate_image(image_data)
    assert is_valid is True

    # Identify Pokemon
    result = await service.identify_pokemon(image_data)

    # Verify result structure
    assert isinstance(result, PokemonIdentification)
    assert result.primary_prediction.pokemon_name in [
        p["name"] for p in MockPokemonClassifier.MOCK_POKEMON_DATA
    ]
    assert 0 <= result.primary_prediction.confidence <= 1
    assert result.processing_time_ms > 0

    # Check model status
    status = await service.get_model_status()
    assert status["status"] == "ready"
