"""
Tests for DeepSeekOCR class.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from deep_ocr import DeepSeekOCR, OCRConfig


class TestDeepSeekOCR:
    """Test cases for DeepSeekOCR."""

    def test_init_with_default_config(self):
        """Test initialization with default config."""
        with (
            patch("deep_ocr.ocr.AutoTokenizer") as mock_tokenizer,
            patch("deep_ocr.ocr.AutoModel") as mock_model,
        ):

            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()

            ocr = DeepSeekOCR()

            assert isinstance(ocr.config, OCRConfig)
            assert ocr.config.model_size == "tiny"

    def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        config = OCRConfig(model_size="large", device="cpu")

        with (
            patch("deep_ocr.ocr.AutoTokenizer") as mock_tokenizer,
            patch("deep_ocr.ocr.AutoModel") as mock_model,
        ):

            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()

            ocr = DeepSeekOCR(config=config)

            assert ocr.config.model_size == "large"
            assert ocr.config.device == "cpu"

    def test_init_with_kwargs(self):
        """Test initialization with kwargs."""
        with (
            patch("deep_ocr.ocr.AutoTokenizer") as mock_tokenizer,
            patch("deep_ocr.ocr.AutoModel") as mock_model,
        ):

            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()

            ocr = DeepSeekOCR(model_size="base", device="cpu")

            assert ocr.config.model_size == "base"
            assert ocr.config.device == "cpu"

    def test_flash_attention_available(self):
        """Test Flash Attention configuration."""
        config = OCRConfig(use_flash_attention=True)
        assert config.use_flash_attention is True

        # Test that the config can be created with flash attention enabled
        with (
            patch("deep_ocr.ocr.AutoTokenizer") as mock_tokenizer,
            patch("deep_ocr.ocr.AutoModel") as mock_model,
        ):

            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()

            ocr = DeepSeekOCR(config=config)
            assert ocr.config.use_flash_attention is True

    def test_flash_attention_unavailable(self):
        """Test Flash Attention when not available."""
        with (
            patch("deep_ocr.ocr.AutoTokenizer") as mock_tokenizer,
            patch("deep_ocr.ocr.AutoModel") as mock_model,
            patch("importlib.import_module", side_effect=ImportError),
        ):

            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()

            config = OCRConfig(use_flash_attention=True)
            ocr = DeepSeekOCR(config=config)

            # Check that flash attention was not requested due to ImportError
            mock_model.from_pretrained.assert_called_once()
            call_args = mock_model.from_pretrained.call_args
            assert "_attn_implementation" not in call_args[1]

    def test_process_file_not_found(self):
        """Test process method with non-existent file."""
        with (
            patch("deep_ocr.ocr.AutoTokenizer") as mock_tokenizer,
            patch("deep_ocr.ocr.AutoModel") as mock_model,
        ):

            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()

            ocr = DeepSeekOCR()

            with pytest.raises(FileNotFoundError):
                ocr.process("non_existent_file.jpg")

    def test_batch_process_with_prompts_tuples(self):
        """Test batch processing with tuple format."""
        with (
            patch("deep_ocr.ocr.AutoTokenizer") as mock_tokenizer,
            patch("deep_ocr.ocr.AutoModel") as mock_model,
            patch.object(DeepSeekOCR, "process") as mock_process,
        ):

            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            mock_process.return_value = Mock()

            ocr = DeepSeekOCR()

            pairs = [("image1.jpg", "prompt1"), ("image2.jpg", "prompt2")]

            results = ocr.batch_process_with_prompts(pairs, "output")

            assert len(results) == 2
            assert mock_process.call_count == 2

    def test_batch_process_with_prompts_dicts(self):
        """Test batch processing with dictionary format."""
        with (
            patch("deep_ocr.ocr.AutoTokenizer") as mock_tokenizer,
            patch("deep_ocr.ocr.AutoModel") as mock_model,
            patch.object(DeepSeekOCR, "process") as mock_process,
        ):

            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()
            mock_process.return_value = Mock()

            ocr = DeepSeekOCR()

            pairs = [
                {"image": "image1.jpg", "prompt": "prompt1"},
                {"image": "image2.jpg", "prompt": "prompt2"},
            ]

            results = ocr.batch_process_with_prompts(pairs, "output")

            assert len(results) == 2
            assert mock_process.call_count == 2

    def test_batch_process_with_prompts_invalid_format(self):
        """Test batch processing with invalid format."""
        with (
            patch("deep_ocr.ocr.AutoTokenizer") as mock_tokenizer,
            patch("deep_ocr.ocr.AutoModel") as mock_model,
        ):

            mock_tokenizer.from_pretrained.return_value = Mock()
            mock_model.from_pretrained.return_value = Mock()

            ocr = DeepSeekOCR()

            pairs = ["invalid_format"]

            with pytest.raises(ValueError):
                ocr.batch_process_with_prompts(pairs, "output")
