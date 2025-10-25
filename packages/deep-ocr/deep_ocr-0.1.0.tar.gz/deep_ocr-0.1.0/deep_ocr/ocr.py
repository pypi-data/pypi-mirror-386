"""
DeepSeek-OCR Model Implementation
A production-ready wrapper for DeepSeek-OCR inference with CPU/GPU support.
"""

import torch
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any
from dataclasses import dataclass
from transformers import AutoModel, AutoTokenizer
import warnings


@dataclass
class OCRConfig:
    """Configuration for DeepSeek-OCR model."""

    # Model configurations
    model_name: str = "deepseek-ai/DeepSeek-OCR"
    device: str = "cpu"
    dtype: torch.dtype = torch.bfloat16
    trust_remote_code: bool = True
    use_flash_attention: bool = False

    # Inference size presets
    model_size: str = "tiny"  # 'tiny', 'small', 'base', 'large', 'gundam'

    # Custom size parameters (overrides model_size if set)
    base_size: Optional[int] = None
    image_size: Optional[int] = None
    crop_mode: Optional[bool] = None

    # Processing options
    test_compress: bool = True
    save_results: bool = True

    def __post_init__(self):
        """Set size parameters based on model_size preset."""
        if self.base_size is None or self.image_size is None or self.crop_mode is None:
            presets = {
                "tiny": (512, 512, False),
                "small": (640, 640, False),
                "base": (1024, 1024, False),
                "large": (1280, 1280, False),
                "gundam": (1024, 640, True),
            }

            if self.model_size.lower() not in presets:
                raise ValueError(
                    f"Invalid model_size. Choose from: {list(presets.keys())}"
                )

            preset_base, preset_img, preset_crop = presets[self.model_size.lower()]

            if self.base_size is None:
                self.base_size = preset_base
            if self.image_size is None:
                self.image_size = preset_img
            if self.crop_mode is None:
                self.crop_mode = preset_crop

        # Adjust dtype for CPU
        if "cuda" not in self.device:
            self.dtype = torch.float32


class DeepSeekOCR:
    """DeepSeek-OCR model wrapper with CPU/GPU support."""

    # Default prompts
    PROMPT_MARKDOWN = "<image>\n<|grounding|>Convert the document to markdown format."
    PROMPT_TEXT = "<image>\n<|grounding|>Extract all text from this image."

    def __init__(
        self,
        config: Optional[OCRConfig] = None,
        model_cache_dir: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize DeepSeek-OCR model.

        Args:
            config: OCRConfig instance
            model_cache_dir: Directory to cache model files
            **kwargs: Additional configuration parameters
        """
        # Create configuration
        if config is None:
            config = OCRConfig(**kwargs)
        else:
            # Update config with any additional kwargs
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)

        self.config = config

        # Adjust dtype for CPU
        if "cuda" not in self.config.device:
            self.config.dtype = torch.float32

        print(f"Initializing DeepSeek-OCR on {self.config.device}...")
        print(
            f"Configuration: {self.config.model_size} "
            f"(base_size={self.config.base_size}, "
            f"image_size={self.config.image_size}, "
            f"crop_mode={self.config.crop_mode})"
        )

        # Load model
        self._load_model(model_cache_dir)

    def _load_model(self, cache_dir: Optional[str]):
        """Load tokenizer and model."""
        kwargs = {
            "trust_remote_code": self.config.trust_remote_code,
        }

        if cache_dir:
            kwargs["cache_dir"] = cache_dir

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name, **kwargs)

        # Load model
        model_kwargs = {
            **kwargs,
            "use_safetensors": True,
        }

        # Configure Flash Attention if available and requested
        if self.config.use_flash_attention:
            try:
                import flash_attn

                model_kwargs["_attn_implementation"] = "flash_attention_2"
                print("⚡ Flash Attention 2 enabled for high performance!")
            except ImportError:
                print(
                    "⚠️  Flash Attention not available. Install with: pip install flash-attn"
                )
                print("   Falling back to standard attention.")

        self.model = AutoModel.from_pretrained(self.config.model_name, **model_kwargs)

        # Move to device and set dtype
        self.model = self.model.eval()
        if "cuda" in self.config.device:
            self.model = self.model.cuda().to(self.config.dtype)
        else:
            self.model = self.model.to(self.config.dtype)

        print("Model loaded successfully!")

    def process(
        self,
        image_path: Union[str, Path],
        prompt: Optional[str] = None,
        output_dir: Union[str, Path] = "output",
        base_size: Optional[int] = None,
        image_size: Optional[int] = None,
        crop_mode: Optional[bool] = None,
        test_compress: Optional[bool] = None,
        save_results: Optional[bool] = None,
    ) -> Any:
        """
        Process an image with OCR.

        Args:
            image_path: Path to the image file
            prompt: Custom prompt for OCR
            output_dir: Directory to save results
            base_size: Override base size
            image_size: Override image size
            crop_mode: Override crop mode
            test_compress: Override test compression
            save_results: Override save results

        Returns:
            OCR result object
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Use provided parameters or fall back to config
        prompt = prompt or self.PROMPT_MARKDOWN
        base_size = base_size or self.config.base_size
        image_size = image_size or self.config.image_size
        crop_mode = crop_mode if crop_mode is not None else self.config.crop_mode
        test_compress = (
            test_compress if test_compress is not None else self.config.test_compress
        )
        save_results = (
            save_results if save_results is not None else self.config.save_results
        )

        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Processing: {image_path.name}")
        print(f"Prompt: {prompt[:50]}...")

        # Run inference
        result = self.model.infer(
            self.tokenizer,
            prompt=prompt,
            image_file=str(image_path),
            output_path=str(output_dir),
            base_size=base_size,
            image_size=image_size,
            crop_mode=crop_mode,
            test_compress=test_compress,
            save_results=save_results,
        )

        print(f"✓ Processing complete! Results saved to: {output_dir}")

        return result

    def ocr_to_markdown(
        self, image_path: Union[str, Path], output_dir: Union[str, Path] = "output"
    ) -> Any:
        """
        Extract text and convert to markdown format.

        Args:
            image_path: Path to the image file
            output_dir: Directory to save results

        Returns:
            Markdown formatted text
        """
        result = self.process(
            image_path, prompt=self.PROMPT_MARKDOWN, output_dir=output_dir
        )
        return result

    def ocr_to_text(
        self, image_path: Union[str, Path], output_dir: Union[str, Path] = "output"
    ) -> Any:
        """
        Extract plain text from image.

        Args:
            image_path: Path to the image file
            output_dir: Directory to save results

        Returns:
            Plain text
        """
        result = self.process(
            image_path, prompt=self.PROMPT_TEXT, output_dir=output_dir
        )
        return result

    def batch_process(
        self,
        image_paths: list,
        output_dir: Union[str, Path],
        prompt: Optional[str] = None,
    ) -> list:
        """
        Process multiple images in batch with the same prompt.

        Args:
            image_paths: List of image paths
            output_dir: Directory to save all results
            prompt: Custom prompt for all images

        Returns:
            List of results for each image
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for i, img_path in enumerate(image_paths, 1):
            print(f"\n[{i}/{len(image_paths)}] Processing {img_path}...")
            try:
                result = self.process(img_path, prompt=prompt, output_dir=output_dir)
                results.append(
                    {"image": img_path, "result": result, "status": "success"}
                )
            except Exception as e:
                print(f"✗ Error processing {img_path}: {e}")
                results.append({"image": img_path, "error": str(e), "status": "failed"})

        return results

    def batch_process_with_prompts(
        self, image_prompt_pairs: list, output_dir: Union[str, Path]
    ) -> list:
        """
        Process multiple images in batch with separate prompts for each image.

        Args:
            image_prompt_pairs: List of tuples (image_path, prompt) or dicts {'image': path, 'prompt': text}
            output_dir: Directory to save all results

        Returns:
            List of results for each image

        Example:
            # Using tuples
            pairs = [
                ("doc/receipt.jpg", "<image>\n<|grounding|>Extract all items and prices."),
                ("doc/invoice.jpg", "<image>\n<|grounding|>Extract company name and total amount."),
                ("doc/document.jpg", "<image>\n<|grounding|>Convert to markdown format.")
            ]
            results = ocr.batch_process_with_prompts(pairs, "batch_output")

            # Using dictionaries
            pairs = [
                {"image": "doc/receipt.jpg", "prompt": "Extract all items and prices."},
                {"image": "doc/invoice.jpg", "prompt": "Extract company name and total amount."},
                {"image": "doc/document.jpg", "prompt": "Convert to markdown format."}
            ]
            results = ocr.batch_process_with_prompts(pairs, "batch_output")
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for i, pair in enumerate(image_prompt_pairs, 1):
            # Handle both tuple and dict formats
            if isinstance(pair, tuple):
                img_path, prompt = pair
            elif isinstance(pair, dict):
                img_path = pair["image"]
                prompt = pair["prompt"]
            else:
                raise ValueError(
                    "Each item must be a tuple (image_path, prompt) or dict {'image': path, 'prompt': text}"
                )

            print(f"\n[{i}/{len(image_prompt_pairs)}] Processing {img_path}...")
            print(f"Prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")

            try:
                result = self.process(img_path, prompt=prompt, output_dir=output_dir)
                results.append(
                    {
                        "image": img_path,
                        "prompt": prompt,
                        "result": result,
                        "status": "success",
                    }
                )
            except Exception as e:
                print(f"✗ Error processing {img_path}: {e}")
                results.append(
                    {
                        "image": img_path,
                        "prompt": prompt,
                        "error": str(e),
                        "status": "failed",
                    }
                )

        return results
