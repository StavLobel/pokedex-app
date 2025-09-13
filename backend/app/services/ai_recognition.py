"""
AI-powered Pokemon recognition service with mock implementation for development.
"""
import asyncio
import hashlib
import io
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

from ..core.config import get_settings
from ..models.ai import (BoundingBox, ImageProcessingConfig,
                         ImageProcessingError, ModelInfo, ModelNotLoadedError,
                         ModelType, PokemonIdentification, Prediction,
                         PredictionError)


class PokemonClassifier(ABC):
    """Abstract base class for Pokemon classification models."""

    def __init__(
        self, config: ImageProcessingConfig, confidence_threshold: float = 0.7
    ):
        self.config = config
        self.confidence_threshold = confidence_threshold
        self._is_loaded = False

    @abstractmethod
    async def load_model(self) -> None:
        """Load the AI model."""
        pass

    @abstractmethod
    async def predict(self, image: np.ndarray) -> List[Prediction]:
        """Make predictions on preprocessed image."""
        pass

    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Get model information and metadata."""
        pass

    async def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess image for model input.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Preprocessed image array

        Raises:
            ImageProcessingError: If image processing fails
        """
        try:
            # Open image with PIL
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Resize to target size
            target_height, target_width = self.config.target_size
            image = image.resize(
                (target_width, target_height), Image.Resampling.LANCZOS
            )

            # Convert to numpy array
            image_array = np.array(image, dtype=np.float32)

            # Normalize pixel values to [0, 1]
            image_array = image_array / 255.0

            # Apply ImageNet normalization
            mean = np.array(self.config.normalize_mean, dtype=np.float32)
            std = np.array(self.config.normalize_std, dtype=np.float32)
            image_array = (image_array - mean) / std

            # Add batch dimension
            image_array = np.expand_dims(image_array, axis=0)

            return image_array

        except Exception as e:
            raise ImageProcessingError(f"Failed to preprocess image: {str(e)}")

    def _calculate_image_hash(self, image_bytes: bytes) -> str:
        """Calculate hash of image for caching."""
        return hashlib.sha256(image_bytes).hexdigest()

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded


class MockPokemonClassifier(PokemonClassifier):
    """Mock Pokemon classifier for development and testing."""

    # Mock Pokemon data for realistic predictions
    MOCK_POKEMON_DATA = [
        {"id": 25, "name": "pikachu"},
        {"id": 1, "name": "bulbasaur"},
        {"id": 4, "name": "charmander"},
        {"id": 7, "name": "squirtle"},
        {"id": 150, "name": "mewtwo"},
        {"id": 6, "name": "charizard"},
        {"id": 9, "name": "blastoise"},
        {"id": 3, "name": "venusaur"},
        {"id": 144, "name": "articuno"},
        {"id": 145, "name": "zapdos"},
        {"id": 146, "name": "moltres"},
        {"id": 151, "name": "mew"},
        {"id": 39, "name": "jigglypuff"},
        {"id": 104, "name": "cubone"},
        {"id": 143, "name": "snorlax"},
        {"id": 94, "name": "gengar"},
        {"id": 130, "name": "gyarados"},
        {"id": 149, "name": "dragonite"},
        {"id": 59, "name": "arcanine"},
        {"id": 65, "name": "alakazam"},
    ]

    def __init__(
        self, config: ImageProcessingConfig, confidence_threshold: float = 0.7
    ):
        super().__init__(config, confidence_threshold)
        self.model_version = "mock-v1.0.0"
        self._prediction_delay_ms = 100  # Simulate processing time

    async def load_model(self) -> None:
        """Load the mock model (simulate loading time)."""
        await asyncio.sleep(0.1)  # Simulate model loading
        self._is_loaded = True

    async def predict(self, image: np.ndarray) -> List[Prediction]:
        """
        Generate mock predictions based on image hash for consistency.

        Args:
            image: Preprocessed image array

        Returns:
            List of predictions sorted by confidence

        Raises:
            ModelNotLoadedError: If model is not loaded
            PredictionError: If prediction fails
        """
        if not self._is_loaded:
            raise ModelNotLoadedError("Mock model is not loaded")

        try:
            # Simulate processing time
            await asyncio.sleep(self._prediction_delay_ms / 1000.0)

            # Generate deterministic predictions based on image content
            # Use image array sum as seed for consistent results
            image_seed = int(np.sum(image) * 1000) % 1000000
            random.seed(image_seed)

            # Select primary prediction
            primary_pokemon = random.choice(self.MOCK_POKEMON_DATA)

            # Generate confidence score (biased towards higher values)
            base_confidence = random.uniform(0.3, 0.95)

            # Create primary prediction
            primary_prediction = Prediction(
                pokemon_name=primary_pokemon["name"],
                pokemon_id=primary_pokemon["id"],
                confidence=base_confidence,
                bounding_box=self._generate_mock_bounding_box(),
            )

            predictions = [primary_prediction]

            # Add alternative predictions if confidence is low
            if base_confidence < self.confidence_threshold:
                num_alternatives = random.randint(2, 4)
                used_ids = {primary_pokemon["id"]}

                for _ in range(num_alternatives):
                    # Select different Pokemon
                    available_pokemon = [
                        p for p in self.MOCK_POKEMON_DATA if p["id"] not in used_ids
                    ]
                    if not available_pokemon:
                        break

                    alt_pokemon = random.choice(available_pokemon)
                    used_ids.add(alt_pokemon["id"])

                    # Generate lower confidence
                    alt_confidence = random.uniform(0.1, base_confidence - 0.05)

                    alt_prediction = Prediction(
                        pokemon_name=alt_pokemon["name"],
                        pokemon_id=alt_pokemon["id"],
                        confidence=alt_confidence,
                        bounding_box=self._generate_mock_bounding_box(),
                    )
                    predictions.append(alt_prediction)

            # Sort by confidence descending
            predictions.sort(key=lambda x: x.confidence, reverse=True)

            return predictions

        except Exception as e:
            raise PredictionError(f"Mock prediction failed: {str(e)}")

    def _generate_mock_bounding_box(self) -> BoundingBox:
        """Generate a realistic mock bounding box."""
        # Generate box that covers most of the image (Pokemon typically fill the frame)
        x = random.uniform(0.1, 0.3)
        y = random.uniform(0.1, 0.3)
        width = random.uniform(0.4, 0.8)
        height = random.uniform(0.4, 0.8)

        # Ensure box doesn't exceed image boundaries
        width = min(width, 1.0 - x)
        height = min(height, 1.0 - y)

        return BoundingBox(x=x, y=y, width=width, height=height)

    def get_model_info(self) -> ModelInfo:
        """Get mock model information."""
        return ModelInfo(
            name="Mock Pokemon Classifier",
            version=self.model_version,
            type=ModelType.MOCK,
            accuracy=0.85,  # Mock accuracy
            input_shape=(*self.config.target_size, 3),
            num_classes=len(self.MOCK_POKEMON_DATA),
            confidence_threshold=self.confidence_threshold,
            created_at=datetime.now().isoformat(),
        )


class ImageRecognitionService:
    """Main service for Pokemon image recognition."""

    def __init__(self):
        self.settings = get_settings()
        self.config = ImageProcessingConfig()
        self.classifier: Optional[PokemonClassifier] = None
        self._initialize_classifier()

    def _initialize_classifier(self) -> None:
        """Initialize the appropriate classifier based on configuration."""
        # For now, always use mock classifier
        # In the future, this will switch based on settings.model_type
        self.classifier = MockPokemonClassifier(
            config=self.config,
            confidence_threshold=self.settings.model_confidence_threshold,
        )

    async def initialize(self) -> None:
        """Initialize the recognition service."""
        if self.classifier and not self.classifier.is_loaded:
            await self.classifier.load_model()

    async def identify_pokemon(self, image_bytes: bytes) -> PokemonIdentification:
        """
        Identify Pokemon in the provided image.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Pokemon identification result

        Raises:
            ModelNotLoadedError: If AI model is not loaded
            ImageProcessingError: If image processing fails
            PredictionError: If prediction fails
        """
        if not self.classifier:
            raise ModelNotLoadedError("No classifier initialized")

        if not self.classifier.is_loaded:
            await self.classifier.load_model()

        start_time = time.time()

        try:
            # Preprocess image
            processed_image = await self.classifier.preprocess_image(image_bytes)

            # Make predictions
            predictions = await self.classifier.predict(processed_image)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Calculate image hash for caching
            image_hash = self.classifier._calculate_image_hash(image_bytes)

            # Create identification result
            primary_prediction = predictions[0]
            alternative_predictions = predictions[1:] if len(predictions) > 1 else []

            return PokemonIdentification(
                primary_prediction=primary_prediction,
                alternative_predictions=alternative_predictions,
                processing_time_ms=processing_time_ms,
                model_version=self.classifier.get_model_info().version,
                image_hash=image_hash,
            )

        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            raise PredictionError(
                f"Pokemon identification failed after {processing_time_ms}ms: {str(e)}"
            )

    async def get_model_status(self) -> dict:
        """Get current model status and information."""
        if not self.classifier:
            return {"status": "not_initialized", "model_info": None, "is_loaded": False}

        model_info = self.classifier.get_model_info()

        return {
            "status": "ready" if self.classifier.is_loaded else "not_loaded",
            "model_info": model_info.model_dump(),
            "is_loaded": self.classifier.is_loaded,
            "config": self.config.model_dump(),
        }

    async def validate_image(self, image_bytes: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate image before processing.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file size
            if len(image_bytes) > self.config.max_file_size:
                return (
                    False,
                    f"Image too large. Maximum size: {self.config.max_file_size / (1024*1024):.1f}MB",
                )

            # Try to open image
            image = Image.open(io.BytesIO(image_bytes))

            # Check format
            if image.format not in self.config.supported_formats:
                return (
                    False,
                    f"Unsupported format: {image.format}. Supported: {', '.join(self.config.supported_formats)}",
                )

            # Check dimensions (minimum size)
            min_size = 32
            if image.width < min_size or image.height < min_size:
                return False, f"Image too small. Minimum size: {min_size}x{min_size}px"

            return True, None

        except Exception as e:
            return False, f"Invalid image file: {str(e)}"


# Global service instance
_recognition_service: Optional[ImageRecognitionService] = None


async def get_recognition_service() -> ImageRecognitionService:
    """Get or create the global recognition service instance."""
    global _recognition_service

    if _recognition_service is None:
        _recognition_service = ImageRecognitionService()
        await _recognition_service.initialize()

    return _recognition_service
