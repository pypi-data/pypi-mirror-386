"""
Deep-OCR: A Python wrapper for DeepSeek-OCR inference.

This package provides a simple interface for using DeepSeek-OCR models
for optical character recognition (OCR) tasks with support for both
CPU and GPU inference.

Example:
    from deep_ocr import DeepSeekOCR, OCRConfig

    # Basic usage
    ocr = DeepSeekOCR()
    result = ocr.process("image.jpg", output_dir="output")

    # Custom configuration
    config = OCRConfig(model_size="large", crop_mode=False)
    ocr = DeepSeekOCR(config=config)
    result = ocr.process("image.jpg", prompt="<image>\nExtract all text.")
"""

__version__ = "0.1.0"
__author__ = "Gershon Omoraka"
__email__ = "gershblocks@gmail.com"

from .ocr import DeepSeekOCR, OCRConfig

__all__ = ["DeepSeekOCR", "OCRConfig", "__version__", "__author__", "__email__"]
