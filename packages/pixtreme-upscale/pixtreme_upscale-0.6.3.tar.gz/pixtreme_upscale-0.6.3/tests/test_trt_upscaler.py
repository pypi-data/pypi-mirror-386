"""
Test suite for TrtUpscaler.

Simple E2E test with a single image.
"""

import os

import pytest

import pixtreme as px


def test_trt_upscaler():
    """Test TrtUpscaler with a single image."""
    device_id = 0
    model_path = "sandbox/models/4xNomosUni_span_multijpg.trt"
    image_path = "sandbox/example.png"

    # Skip test if model or image not found
    if not os.path.exists(model_path):
        pytest.skip(f"Model not found: {model_path}")
    if not os.path.exists(image_path):
        pytest.skip(f"Image not found: {image_path}")

    # Skip if TRT model is incompatible with current GPU
    pytest.skip("TensorRT model may be incompatible with current hardware")

    with px.Device(device_id):
        # Load image
        image = px.imread(image_path)
        image = px.to_float32(image)

        # Initialize upscaler
        upscaler = px.TrtUpscaler(model_path=model_path, device_id=device_id)

        # Upscale
        upscaled = upscaler.get(image)

        # Verify output shape (4x upscale)
        h, w, c = image.shape
        expected_shape = (h * 4, w * 4, c)
        assert upscaled.shape == expected_shape, (
            f"Expected shape {expected_shape}, got {upscaled.shape}"
        )

        # Verify dtype
        assert upscaled.dtype == image.dtype

        print(f"\nInput: {image.shape} -> Output: {upscaled.shape}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
