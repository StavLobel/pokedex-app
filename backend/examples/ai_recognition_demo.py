#!/usr/bin/env python3
"""
Demo script for the AI recognition service.
Shows how to use the mock Pokemon classifier for development.
"""
import asyncio
import io
import sys
from pathlib import Path

from PIL import Image

# Add the parent directory to the path so we can import from app
sys.path.append(str(Path(__file__).parent.parent))

from app.models.ai import ImageProcessingConfig
from app.services.ai_recognition import get_recognition_service


async def create_sample_image() -> bytes:
    """Create a sample image for testing."""
    # Create a simple colored image
    image = Image.new("RGB", (300, 300), color="yellow")

    # Add some simple shapes to make it more interesting
    from PIL import ImageDraw

    draw = ImageDraw.Draw(image)

    # Draw a simple "Pokemon-like" shape
    draw.ellipse([50, 50, 250, 250], fill="red", outline="black", width=3)
    draw.ellipse([100, 100, 150, 150], fill="black")  # Eye
    draw.ellipse([150, 100, 200, 150], fill="black")  # Eye
    draw.arc([75, 175, 225, 225], start=0, end=180, fill="black", width=3)  # Smile

    # Convert to bytes
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="JPEG", quality=90)
    return img_bytes.getvalue()


async def demo_ai_recognition():
    """Demonstrate the AI recognition service functionality."""
    print("🔥 Pokemon AI Recognition Service Demo")
    print("=" * 50)

    try:
        # Get the recognition service
        print("📡 Initializing AI recognition service...")
        service = await get_recognition_service()

        # Check model status
        print("\n📊 Model Status:")
        status = await service.get_model_status()
        print(f"  Status: {status['status']}")
        print(
            f"  Model: {status['model_info']['name']} v{status['model_info']['version']}"
        )
        print(f"  Type: {status['model_info']['type']}")
        print(f"  Accuracy: {status['model_info']['accuracy']:.1%}")
        print(f"  Classes: {status['model_info']['num_classes']}")
        print(f"  Input Shape: {status['model_info']['input_shape']}")

        # Create a sample image
        print("\n🖼️  Creating sample image...")
        image_bytes = await create_sample_image()
        print(f"  Image size: {len(image_bytes):,} bytes")

        # Validate the image
        print("\n✅ Validating image...")
        is_valid, error = await service.validate_image(image_bytes)
        if is_valid:
            print("  ✓ Image validation passed")
        else:
            print(f"  ✗ Image validation failed: {error}")
            return

        # Identify Pokemon
        print("\n🔍 Identifying Pokemon...")
        result = await service.identify_pokemon(image_bytes)

        print(f"\n🎯 Recognition Results:")
        print(f"  Processing Time: {result.processing_time_ms}ms")
        print(f"  Model Version: {result.model_version}")
        print(f"  Image Hash: {result.image_hash[:16]}...")

        # Primary prediction
        primary = result.primary_prediction
        print(f"\n🥇 Primary Prediction:")
        print(f"  Pokemon: {primary.pokemon_name.title()}")
        print(f"  ID: #{primary.pokemon_id}")
        print(f"  Confidence: {primary.confidence:.1%}")
        print(f"  Confidence Level: {primary.confidence_level.value}")

        if primary.bounding_box:
            bbox = primary.bounding_box
            print(
                f"  Bounding Box: ({bbox.x:.2f}, {bbox.y:.2f}) - {bbox.width:.2f}x{bbox.height:.2f}"
            )

        # Alternative predictions
        if result.alternative_predictions:
            print(
                f"\n🥈 Alternative Predictions ({len(result.alternative_predictions)}):"
            )
            for i, alt in enumerate(result.alternative_predictions, 1):
                print(
                    f"  {i}. {alt.pokemon_name.title()} (#{alt.pokemon_id}) - {alt.confidence:.1%}"
                )

        # Analysis
        print(f"\n📈 Analysis:")
        print(f"  High Confidence: {'Yes' if result.has_high_confidence else 'No'}")
        print(
            f"  Needs User Selection: {'Yes' if result.needs_user_selection else 'No'}"
        )

        # Test multiple images for consistency
        print(f"\n🔄 Testing prediction consistency...")
        result2 = await service.identify_pokemon(image_bytes)

        if (
            result.primary_prediction.pokemon_name
            == result2.primary_prediction.pokemon_name
        ):
            print("  ✓ Predictions are consistent")
        else:
            print("  ✗ Predictions are inconsistent")
            print(f"    First: {result.primary_prediction.pokemon_name}")
            print(f"    Second: {result2.primary_prediction.pokemon_name}")

        # Test with different image
        print(f"\n🎨 Testing with different image...")
        # Create a different colored image
        blue_image = Image.new("RGB", (200, 200), color="blue")
        blue_bytes = io.BytesIO()
        blue_image.save(blue_bytes, format="PNG")

        result3 = await service.identify_pokemon(blue_bytes.getvalue())
        print(
            f"  Different Image Result: {result3.primary_prediction.pokemon_name.title()} ({result3.primary_prediction.confidence:.1%})"
        )

        print(f"\n✨ Demo completed successfully!")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()


async def demo_image_preprocessing():
    """Demonstrate image preprocessing functionality."""
    print("\n🔧 Image Preprocessing Demo")
    print("=" * 30)

    try:
        service = await get_recognition_service()

        # Test different image formats and sizes
        test_cases = [
            ("JPEG 300x300", Image.new("RGB", (300, 300), "red"), "JPEG"),
            ("PNG 150x150", Image.new("RGB", (150, 150), "green"), "PNG"),
            ("Large 1000x800", Image.new("RGB", (1000, 800), "blue"), "JPEG"),
            ("Small 50x50", Image.new("RGB", (50, 50), "yellow"), "PNG"),
            ("RGBA to RGB", Image.new("RGBA", (200, 200), (255, 0, 255, 128)), "PNG"),
        ]

        for name, image, format_type in test_cases:
            print(f"\n  Testing {name}:")

            # Convert to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format=format_type)
            image_data = img_bytes.getvalue()

            print(
                f"    Original: {image.size[0]}x{image.size[1]} {image.mode}, {len(image_data):,} bytes"
            )

            # Validate
            is_valid, error = await service.validate_image(image_data)
            if not is_valid:
                print(f"    ✗ Validation failed: {error}")
                continue

            # Preprocess
            processed = await service.classifier.preprocess_image(image_data)
            print(f"    Processed: {processed.shape}, dtype: {processed.dtype}")
            print(f"    Value range: [{processed.min():.3f}, {processed.max():.3f}]")
            print(f"    ✓ Preprocessing successful")

    except Exception as e:
        print(f"    ❌ Preprocessing demo failed: {e}")


if __name__ == "__main__":
    print("Starting Pokemon AI Recognition Demo...\n")

    # Run the main demo
    asyncio.run(demo_ai_recognition())

    # Run preprocessing demo
    asyncio.run(demo_image_preprocessing())

    print("\n🎉 All demos completed!")
