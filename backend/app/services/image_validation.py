"""
Image validation and preprocessing service
"""

import hashlib
import io
import os
from typing import List, Optional, Tuple

import numpy as np
import structlog
from fastapi import HTTPException, UploadFile
from PIL import Image, ImageOps

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class ImageValidationError(Exception):
    """Custom exception for image validation errors"""

    def __init__(self, message: str, error_code: str):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ImageValidationService:
    """Service for validating and preprocessing uploaded images"""

    def __init__(self):
        self.max_file_size = settings.max_file_size
        self.allowed_mime_types = settings.allowed_file_types
        self.target_size = (224, 224)  # Standard size for most CNN models

    async def validate_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file for type, size, and format

        Args:
            file: FastAPI UploadFile object

        Raises:
            ImageValidationError: If validation fails
        """
        # Check file size
        if file.size and file.size > self.max_file_size:
            raise ImageValidationError(
                f"File size {file.size} bytes exceeds maximum allowed size of {self.max_file_size} bytes",
                "FILE_TOO_LARGE",
            )

        # Check MIME type
        if file.content_type not in self.allowed_mime_types:
            raise ImageValidationError(
                f"File type '{file.content_type}' not supported. Allowed types: {', '.join(self.allowed_mime_types)}",
                "INVALID_FILE_TYPE",
            )

        # Validate file has content
        if not file.filename:
            raise ImageValidationError(
                "No file provided or filename is empty", "NO_FILE_PROVIDED"
            )

        logger.info(
            "File validation passed",
            filename=file.filename,
            content_type=file.content_type,
            size=file.size,
        )

    async def read_and_validate_image(
        self, file: UploadFile
    ) -> Tuple[bytes, Image.Image]:
        """
        Read file content and validate it's a valid image

        Args:
            file: FastAPI UploadFile object

        Returns:
            Tuple of (raw_bytes, PIL_Image)

        Raises:
            ImageValidationError: If image is invalid or corrupted
        """
        try:
            # Read file content
            content = await file.read()

            # Validate actual file size after reading
            if len(content) > self.max_file_size:
                raise ImageValidationError(
                    f"File size {len(content)} bytes exceeds maximum allowed size of {self.max_file_size} bytes",
                    "FILE_TOO_LARGE",
                )

            # Try to open and validate image
            image = Image.open(io.BytesIO(content))

            # Verify image can be loaded (this will raise exception if corrupted)
            image.verify()

            # Reopen image for processing (verify() closes the image)
            image = Image.open(io.BytesIO(content))

            # Check image dimensions (minimum size check)
            if image.width < 32 or image.height < 32:
                raise ImageValidationError(
                    f"Image dimensions {image.width}x{image.height} are too small. Minimum size is 32x32 pixels",
                    "IMAGE_TOO_SMALL",
                )

            # Check for extremely large images that might cause memory issues
            max_pixels = 4096 * 4096  # 16MP limit
            if image.width * image.height > max_pixels:
                raise ImageValidationError(
                    f"Image dimensions {image.width}x{image.height} are too large. Maximum is {max_pixels} pixels",
                    "IMAGE_TOO_LARGE",
                )

            logger.info(
                "Image validation successful",
                filename=file.filename,
                format=image.format,
                mode=image.mode,
                size=f"{image.width}x{image.height}",
                content_size=len(content),
            )

            return content, image

        except ImageValidationError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            logger.error(
                "Image validation failed",
                filename=file.filename,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ImageValidationError(
                f"Invalid or corrupted image file: {str(e)}", "INVALID_IMAGE_FORMAT"
            )

    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        """
        Preprocess image for AI model inference

        Args:
            image: PIL Image object

        Returns:
            Preprocessed image as numpy array
        """
        try:
            # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Resize image to target size while maintaining aspect ratio
            image = ImageOps.fit(image, self.target_size, Image.Resampling.LANCZOS)

            # Convert to numpy array
            img_array = np.array(image, dtype=np.float32)

            # Normalize pixel values to [0, 1] range
            img_array = img_array / 255.0

            # Add batch dimension and rearrange to CHW format (channels first)
            # Shape: (1, 3, 224, 224) for PyTorch models
            img_array = np.transpose(img_array, (2, 0, 1))
            img_array = np.expand_dims(img_array, axis=0)

            logger.info(
                "Image preprocessing completed",
                original_mode=image.mode,
                target_size=self.target_size,
                output_shape=img_array.shape,
                dtype=img_array.dtype,
            )

            return img_array

        except Exception as e:
            logger.error(
                "Image preprocessing failed", error=str(e), error_type=type(e).__name__
            )
            raise ImageValidationError(
                f"Failed to preprocess image: {str(e)}", "PREPROCESSING_ERROR"
            )

    def calculate_image_hash(self, content: bytes) -> str:
        """
        Calculate SHA-256 hash of image content for caching

        Args:
            content: Raw image bytes

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content).hexdigest()

    def get_supported_formats(self) -> List[str]:
        """Get list of supported image formats"""
        return self.allowed_mime_types.copy()

    def get_max_file_size(self) -> int:
        """Get maximum allowed file size in bytes"""
        return self.max_file_size

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


# Global service instance
image_validation_service = ImageValidationService()
