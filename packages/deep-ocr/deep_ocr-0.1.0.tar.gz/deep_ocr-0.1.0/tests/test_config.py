"""
Tests for OCRConfig class.
"""

import pytest
import torch
from deep_ocr import OCRConfig


class TestOCRConfig:
    """Test cases for OCRConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OCRConfig()

        assert config.model_name == "deepseek-ai/DeepSeek-OCR"
        assert config.device == "cpu"
        # CPU automatically sets dtype to float32
        assert config.dtype == torch.float32
        assert config.trust_remote_code is True
        assert config.use_flash_attention is False
        assert config.model_size == "tiny"
        assert config.test_compress is True
        assert config.save_results is True

    def test_model_size_presets(self):
        """Test model size presets."""
        presets = ["tiny", "small", "base", "large", "gundam"]

        for preset in presets:
            config = OCRConfig(model_size=preset)
            assert config.model_size == preset
            assert config.base_size is not None
            assert config.image_size is not None
            assert config.crop_mode is not None

    def test_invalid_model_size(self):
        """Test invalid model size raises error."""
        with pytest.raises(ValueError):
            OCRConfig(model_size="invalid")

    def test_custom_parameters(self):
        """Test custom parameter overrides."""
        config = OCRConfig(
            model_size="tiny", base_size=1024, image_size=768, crop_mode=True
        )

        assert config.base_size == 1024
        assert config.image_size == 768
        assert config.crop_mode is True

    def test_cpu_dtype_override(self):
        """Test that CPU automatically sets dtype to float32."""
        config = OCRConfig(device="cpu")
        assert config.dtype == torch.float32

    def test_cuda_dtype_preserved(self):
        """Test that CUDA preserves bfloat16 dtype."""
        config = OCRConfig(device="cuda:0")
        assert config.dtype == torch.bfloat16
