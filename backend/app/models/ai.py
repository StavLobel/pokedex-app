"""
AI recognition models and data structures.
"""
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import BaseModel, Field, field_validator


class ModelType(str, Enum):
    """AI model types."""

    MOCK = "mock"
    PYTORCH = "pytorch"
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"


class PredictionConfidence(str, Enum):
    """Prediction confidence levels."""

    HIGH = "high"  # >= 0.7
    MEDIUM = "medium"  # 0.4 - 0.69
    LOW = "low"  # < 0.4


class BoundingBox(BaseModel):
    """Bounding box coordinates for object detection."""

    x: float = Field(..., ge=0, le=1, description="X coordinate (normalized 0-1)")
    y: float = Field(..., ge=0, le=1, description="Y coordinate (normalized 0-1)")
    width: float = Field(..., ge=0, le=1, description="Width (normalized 0-1)")
    height: float = Field(..., ge=0, le=1, description="Height (normalized 0-1)")


class Prediction(BaseModel):
    """Single Pokemon prediction result."""

    pokemon_name: str = Field(..., description="Predicted Pokemon name")
    pokemon_id: int = Field(..., gt=0, description="Pokemon ID from Pokedex")
    confidence: float = Field(
        ..., ge=0, le=1, description="Prediction confidence (0-1)"
    )
    bounding_box: Optional[BoundingBox] = Field(
        None, description="Object detection bounding box"
    )

    @field_validator("pokemon_name")
    @classmethod
    def validate_pokemon_name(cls, v):
        """Ensure Pokemon name is valid."""
        if not v or not v.strip():
            raise ValueError("Pokemon name cannot be empty")
        return v.lower().strip()

    @property
    def confidence_level(self) -> PredictionConfidence:
        """Get confidence level category."""
        if self.confidence >= 0.7:
            return PredictionConfidence.HIGH
        elif self.confidence >= 0.4:
            return PredictionConfidence.MEDIUM
        else:
            return PredictionConfidence.LOW


class PokemonIdentification(BaseModel):
    """Complete Pokemon identification result."""

    primary_prediction: Prediction = Field(..., description="Most likely Pokemon match")
    alternative_predictions: List[Prediction] = Field(
        default_factory=list,
        description="Alternative matches for low confidence predictions",
    )
    processing_time_ms: int = Field(
        ..., ge=0, description="Processing time in milliseconds"
    )
    model_version: str = Field(..., description="AI model version used")
    image_hash: Optional[str] = Field(None, description="Hash of processed image")

    @field_validator("alternative_predictions")
    @classmethod
    def validate_alternatives(cls, v, info):
        """Ensure alternatives are sorted by confidence."""
        if v:
            # Sort by confidence descending
            v.sort(key=lambda x: x.confidence, reverse=True)
            # Limit to top 3 alternatives
            v = v[:3]
        return v

    @property
    def has_high_confidence(self) -> bool:
        """Check if primary prediction has high confidence."""
        return self.primary_prediction.confidence >= 0.7

    @property
    def needs_user_selection(self) -> bool:
        """Check if user needs to select from alternatives."""
        return not self.has_high_confidence and len(self.alternative_predictions) > 0


class ModelInfo(BaseModel):
    """AI model information and metadata."""

    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    type: ModelType = Field(..., description="Model type")
    accuracy: Optional[float] = Field(
        None, ge=0, le=1, description="Model accuracy on test set"
    )
    input_shape: tuple = Field(
        ..., description="Expected input image shape (height, width, channels)"
    )
    num_classes: int = Field(..., gt=0, description="Number of Pokemon classes")
    confidence_threshold: float = Field(
        default=0.7, ge=0, le=1, description="Minimum confidence threshold"
    )
    created_at: Optional[str] = Field(None, description="Model creation timestamp")

    model_config = {"arbitrary_types_allowed": True}


class ImageProcessingConfig(BaseModel):
    """Configuration for image preprocessing."""

    target_size: tuple = Field(
        default=(224, 224), description="Target image size (height, width)"
    )
    normalize_mean: List[float] = Field(
        default=[0.485, 0.456, 0.406], description="Normalization mean values"
    )
    normalize_std: List[float] = Field(
        default=[0.229, 0.224, 0.225], description="Normalization std values"
    )
    max_file_size: int = Field(
        default=10 * 1024 * 1024, description="Maximum file size in bytes"
    )
    supported_formats: List[str] = Field(
        default=["JPEG", "PNG", "WebP"], description="Supported image formats"
    )


class AIServiceError(Exception):
    """Base exception for AI service errors."""

    pass


class ModelNotLoadedError(AIServiceError):
    """Raised when AI model is not loaded."""

    pass


class ImageProcessingError(AIServiceError):
    """Raised when image processing fails."""

    pass


class PredictionError(AIServiceError):
    """Raised when prediction fails."""

    pass
