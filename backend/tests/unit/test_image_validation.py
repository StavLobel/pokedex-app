"""
Unit tests for image validation service
"""
import io
import pytest
from unittest.mock import Mock, AsyncMock
from PIL import Image
import numpy as np
from faker import Faker

from app.services.image_validation import ImageValidationService, ImageValidationError

fake = Faker()


class TestFileValidation:
    """Test file validation functionality"""
    
    @pytest.mark.asyncio
    async def test_validate_valid_jpeg_file(self, image_validation_service, valid_jpeg_file):
        """Test validation passes for valid JPEG file"""
        # Should not raise any exception
        await image_validation_service.validate_file(valid_jpeg_file)
    
    @pytest.mark.asyncio
    async def test_validate_valid_png_file(self, image_validation_service, valid_png_file):
        """Test validation passes for valid PNG file"""
        # Should not raise any exception
        await image_validation_service.validate_file(valid_png_file)
    
    @pytest.mark.asyncio
    async def test_validate_file_too_large(self, image_validation_service, large_file):
        """Test validation fails for oversized file"""
        with pytest.raises(ImageValidationError) as exc_info:
            await image_validation_service.validate_file(large_file)
        
        assert exc_info.value.error_code == "FILE_TOO_LARGE"
        assert "exceeds maximum allowed size" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_validate_invalid_file_type(self, image_validation_service, invalid_type_file):
        """Test validation fails for unsupported file type"""
        with pytest.raises(ImageValidationError) as exc_info:
            await image_validation_service.validate_file(invalid_type_file)
        
        assert exc_info.value.error_code == "INVALID_FILE_TYPE"
        assert "not supported" in exc_info.value.message
    
    @pytest.mark.asyncio
    async def test_validate_no_filename(self, image_validation_service, no_filename_file):
        """Test validation fails for file with no filename"""
        with pytest.raises(ImageValidationError) as exc_info:
            await image_validation_service.validate_file(no_filename_file)
        
        assert exc_info.value.error_code == "NO_FILE_PROVIDED"
        assert "No file provided" in exc_info.value.message


class TestImageReading:
    """Test image reading and validation functionality"""
    
    @pytest.mark.asyncio
    async def test_read_valid_image(self, image_validation_service, valid_jpeg_file):
        """Test reading valid image returns content and PIL image"""
        content, image = await image_validation_service.read_and_validate_image(valid_jpeg_file)
        
        assert isinstance(content, bytes)
        assert len(content) > 0
        assert isinstance(image, Image.Image)
        assert image.width == 100
        assert image.height == 100
        assert image.mode == 'RGB'
    
    @pytest.mark.asyncio
    async def test_read_corrupted_image(self, image_validation_service, corrupted_image_file):
        """Test reading corrupted image raises validation error"""
        with pytest.raises(ImageValidationError) as exc_info:
            await image_validation_service.read_and_validate_image(corrupted_image_file)
        
        assert exc_info.value.error_code == "INVALID_IMAGE_FORMAT"
    
    @pytest.mark.asyncio
    async def test_read_image_too_small(self, image_validation_service, tiny_image_file):
        """Test reading image with dimensions too small"""
        with pytest.raises(ImageValidationError) as exc_info:
            await image_validation_service.read_and_validate_image(tiny_image_file)
        
        assert exc_info.value.error_code == "IMAGE_TOO_SMALL"
    
    @pytest.mark.asyncio
    async def test_read_image_content_size_validation(self, image_validation_service):
        """Test content size validation after reading"""
        # Create a large image that would exceed size limit
        img = Image.new('RGB', (3000, 3000), color=fake.color())
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=100)
        content_size = len(img_bytes.getvalue())
        
        # Mock the file to report smaller size initially but larger after reading
        file = Mock()
        file.filename = fake.file_name(extension='jpg')
        file.content_type = "image/jpeg"
        file.size = fake.random_int(min=1024, max=2048)  # Report small size initially
        file.read = AsyncMock(return_value=img_bytes.getvalue())
        
        # Temporarily reduce max file size for this test
        original_max_size = image_validation_service.max_file_size
        image_validation_service.max_file_size = content_size - 1000  # Set limit below actual size
        
        try:
            with pytest.raises(ImageValidationError) as exc_info:
                await image_validation_service.read_and_validate_image(file)
            
            assert exc_info.value.error_code == "FILE_TOO_LARGE"
        finally:
            image_validation_service.max_file_size = original_max_size


class TestImagePreprocessing:
    """Test image preprocessing functionality"""
    
    def test_preprocess_rgb_image(self, image_validation_service, rgb_image):
        """Test preprocessing RGB image"""
        result = image_validation_service.preprocess_image(rgb_image)
        
        # Check output shape: (1, 3, 224, 224) - batch, channels, height, width
        assert result.shape == (1, 3, 224, 224)
        assert result.dtype == np.float32
        
        # Check normalization (values should be between 0 and 1)
        assert np.all(result >= 0.0)
        assert np.all(result <= 1.0)
    
    def test_preprocess_rgba_image(self, image_validation_service, rgba_image):
        """Test preprocessing RGBA image (should convert to RGB)"""
        result = image_validation_service.preprocess_image(rgba_image)
        
        assert result.shape == (1, 3, 224, 224)
        assert result.dtype == np.float32
    
    def test_preprocess_grayscale_image(self, image_validation_service, grayscale_image):
        """Test preprocessing grayscale image (should convert to RGB)"""
        result = image_validation_service.preprocess_image(grayscale_image)
        
        assert result.shape == (1, 3, 224, 224)
        assert result.dtype == np.float32
    
    def test_preprocess_different_aspect_ratios(self, image_validation_service, wide_image, tall_image, square_image):
        """Test preprocessing images with different aspect ratios"""
        # Wide image
        wide_result = image_validation_service.preprocess_image(wide_image)
        assert wide_result.shape == (1, 3, 224, 224)
        
        # Tall image
        tall_result = image_validation_service.preprocess_image(tall_image)
        assert tall_result.shape == (1, 3, 224, 224)
        
        # Square image
        square_result = image_validation_service.preprocess_image(square_image)
        assert square_result.shape == (1, 3, 224, 224)


class TestUtilityMethods:
    """Test utility methods"""
    
    def test_calculate_image_hash(self, image_validation_service, random_bytes):
        """Test image hash calculation"""
        content1 = random_bytes
        content2 = fake.binary(length=fake.random_int(min=100, max=1000))
        
        hash1 = image_validation_service.calculate_image_hash(content1)
        hash2 = image_validation_service.calculate_image_hash(content2)
        
        # Hashes should be different for different content
        assert hash1 != hash2
        
        # Same content should produce same hash
        hash1_repeat = image_validation_service.calculate_image_hash(content1)
        assert hash1 == hash1_repeat
        
        # Hash should be 64 characters (SHA-256 hex)
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1)
    
    def test_get_supported_formats(self, image_validation_service):
        """Test getting supported formats"""
        formats = image_validation_service.get_supported_formats()
        
        assert isinstance(formats, list)
        assert "image/jpeg" in formats
        assert "image/png" in formats
        assert "image/webp" in formats
    
    def test_get_max_file_size(self, image_validation_service):
        """Test getting max file size"""
        max_size = image_validation_service.get_max_file_size()
        
        assert isinstance(max_size, int)
        assert max_size > 0
    
    def test_format_file_size(self, image_validation_service):
        """Test file size formatting"""
        # Test bytes
        size_bytes = fake.random_int(min=100, max=1023)
        result = image_validation_service.format_file_size(size_bytes)
        assert result.endswith(" B")
        
        # Test kilobytes
        size_kb = fake.random_int(min=1024, max=1024*1024-1)
        result = image_validation_service.format_file_size(size_kb)
        assert result.endswith(" KB")
        
        # Test megabytes
        size_mb = fake.random_int(min=1024*1024, max=10*1024*1024)
        result = image_validation_service.format_file_size(size_mb)
        assert result.endswith(" MB")


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_image_validation_error_creation(self):
        """Test ImageValidationError creation"""
        message = fake.sentence()
        code = fake.word().upper()
        error = ImageValidationError(message, code)
        
        assert error.message == message
        assert error.error_code == code
        assert str(error) == message
    
    def test_preprocessing_error_handling(self, image_validation_service):
        """Test preprocessing error handling with invalid input"""
        # This should raise an error when trying to preprocess None
        with pytest.raises(ImageValidationError) as exc_info:
            image_validation_service.preprocess_image(None)
        
        assert exc_info.value.error_code == "PREPROCESSING_ERROR"


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple operations"""
    
    @pytest.mark.asyncio
    async def test_complete_validation_and_preprocessing_flow(self, image_validation_service, valid_jpeg_file):
        """Test complete flow from file validation to preprocessing"""
        # Step 1: Validate file
        await image_validation_service.validate_file(valid_jpeg_file)
        
        # Step 2: Read and validate image
        content, image = await image_validation_service.read_and_validate_image(valid_jpeg_file)
        
        # Step 3: Calculate hash
        image_hash = image_validation_service.calculate_image_hash(content)
        
        # Step 4: Preprocess image
        processed = image_validation_service.preprocess_image(image)
        
        # Verify all steps completed successfully
        assert len(content) > 0
        assert isinstance(image, Image.Image)
        assert len(image_hash) == 64
        assert processed.shape == (1, 3, 224, 224)
    
    @pytest.mark.asyncio
    async def test_webp_image_support(self, image_validation_service, valid_webp_file):
        """Test WebP image format support"""
        # Should validate and process successfully
        await image_validation_service.validate_file(valid_webp_file)
        content, image = await image_validation_service.read_and_validate_image(valid_webp_file)
        processed = image_validation_service.preprocess_image(image)
        
        assert processed.shape == (1, 3, 224, 224)