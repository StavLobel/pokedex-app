"""
Pokemon identification API endpoints
"""

import time
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.image_validation import ImageValidationError, image_validation_service

logger = structlog.get_logger(__name__)
router = APIRouter()
settings = get_settings()


class PokemonMatch(BaseModel):
    """Model for individual Pokemon match result"""

    name: str = Field(..., description="Pokemon name")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score between 0 and 1"
    )
    pokemon_id: int = Field(..., gt=0, description="Pokemon ID from Pokedex")


class PokemonIdentificationResponse(BaseModel):
    """Response model for Pokemon identification"""

    success: bool = Field(..., description="Whether the identification was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Identification results")
    error: Optional[Dict[str, str]] = Field(
        None, description="Error information if identification failed"
    )
    processing_time_ms: float = Field(
        ..., description="Processing time in milliseconds"
    )
    timestamp: float = Field(..., description="Response timestamp")
    request_id: str = Field(..., description="Unique request identifier")


class ImageUploadStats(BaseModel):
    """Model for image upload statistics"""

    filename: str
    content_type: str
    size_bytes: int
    size_formatted: str
    image_hash: str
    dimensions: str
    format: str


async def get_request_id() -> str:
    """Generate unique request ID for tracking"""
    return f"req_{int(time.time() * 1000000)}"


@router.post("/identify", response_model=PokemonIdentificationResponse)
async def identify_pokemon(
    image: UploadFile = File(
        ...,
        description="Image file containing a Pokemon (JPEG, PNG, or WebP, max 10MB)",
    ),
    request_id: str = Depends(get_request_id),
) -> PokemonIdentificationResponse:
    """
    Identify Pokemon from uploaded image using AI recognition.

    This endpoint accepts image files and processes them through an AI model
    to identify the Pokemon in the image. The response includes the identified
    Pokemon information or multiple candidates if confidence is low.

    Args:
        image: Uploaded image file (JPEG, PNG, or WebP format, max 10MB)
        request_id: Auto-generated unique request identifier

    Returns:
        PokemonIdentificationResponse: Identification results with Pokemon data

    Raises:
        HTTPException: For validation errors, processing failures, or service unavailability
    """
    start_time = time.time()

    logger.info(
        "Pokemon identification request started",
        request_id=request_id,
        filename=image.filename,
        content_type=image.content_type,
        size=image.size,
    )

    try:
        # Step 1: Validate the uploaded file
        await image_validation_service.validate_file(image)

        # Step 2: Read and validate image content
        (
            image_content,
            pil_image,
        ) = await image_validation_service.read_and_validate_image(image)

        # Step 3: Calculate image hash for potential caching
        image_hash = image_validation_service.calculate_image_hash(image_content)

        # Step 4: Preprocess image for AI model
        processed_image = image_validation_service.preprocess_image(pil_image)

        # Create upload statistics
        upload_stats = ImageUploadStats(
            filename=image.filename,
            content_type=image.content_type,
            size_bytes=len(image_content),
            size_formatted=image_validation_service.format_file_size(
                len(image_content)
            ),
            image_hash=image_hash,
            dimensions=f"{pil_image.width}x{pil_image.height}",
            format=pil_image.format or "Unknown",
        )

        logger.info(
            "Image validation and preprocessing completed",
            request_id=request_id,
            upload_stats=upload_stats.model_dump(),
            processed_shape=processed_image.shape,
        )

        # TODO: Step 5: Send to AI model for identification (will be implemented in task 5)
        # For now, return a mock response indicating successful preprocessing

        processing_time = (time.time() - start_time) * 1000

        # Mock response for successful preprocessing
        response_data = {
            "message": "Image successfully validated and preprocessed",
            "upload_stats": upload_stats.model_dump(),
            "preprocessing": {
                "target_size": "224x224",
                "format": "RGB",
                "normalized": True,
                "shape": list(processed_image.shape),
            },
            "next_step": "AI model identification (to be implemented)",
        }

        logger.info(
            "Pokemon identification request completed successfully",
            request_id=request_id,
            processing_time_ms=processing_time,
        )

        return PokemonIdentificationResponse(
            success=True,
            data=response_data,
            error=None,
            processing_time_ms=round(processing_time, 2),
            timestamp=time.time(),
            request_id=request_id,
        )

    except ImageValidationError as e:
        processing_time = (time.time() - start_time) * 1000

        logger.warning(
            "Image validation failed",
            request_id=request_id,
            error_code=e.error_code,
            error_message=e.message,
            processing_time_ms=processing_time,
        )

        # Map validation errors to appropriate HTTP status codes
        status_code_map = {
            "FILE_TOO_LARGE": 413,
            "INVALID_FILE_TYPE": 400,
            "NO_FILE_PROVIDED": 400,
            "IMAGE_TOO_SMALL": 400,
            "IMAGE_TOO_LARGE": 400,
            "INVALID_IMAGE_FORMAT": 400,
            "PREPROCESSING_ERROR": 422,
        }

        status_code = status_code_map.get(e.error_code, 400)

        return PokemonIdentificationResponse(
            success=False,
            data=None,
            error={
                "code": e.error_code,
                "message": e.message,
                "supported_formats": ", ".join(
                    image_validation_service.get_supported_formats()
                ),
                "max_file_size": image_validation_service.format_file_size(
                    image_validation_service.get_max_file_size()
                ),
            },
            processing_time_ms=round(processing_time, 2),
            timestamp=time.time(),
            request_id=request_id,
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000

        logger.error(
            "Unexpected error during Pokemon identification",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            processing_time_ms=processing_time,
        )

        return PokemonIdentificationResponse(
            success=False,
            data=None,
            error={
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while processing the image. Please try again.",
                "details": str(e) if settings.debug else None,
            },
            processing_time_ms=round(processing_time, 2),
            timestamp=time.time(),
            request_id=request_id,
        )


@router.get("/identify/info")
async def get_upload_info():
    """
    Get information about image upload requirements and limitations.

    Returns:
        Dict with upload requirements, supported formats, and size limits
    """
    return {
        "supported_formats": image_validation_service.get_supported_formats(),
        "max_file_size_bytes": image_validation_service.get_max_file_size(),
        "max_file_size_formatted": image_validation_service.format_file_size(
            image_validation_service.get_max_file_size()
        ),
        "target_image_size": "224x224 pixels",
        "minimum_image_size": "32x32 pixels",
        "preprocessing": {
            "format_conversion": "Converts all images to RGB format",
            "resizing": "Resizes to 224x224 while maintaining aspect ratio",
            "normalization": "Normalizes pixel values to 0-1 range",
        },
    }
