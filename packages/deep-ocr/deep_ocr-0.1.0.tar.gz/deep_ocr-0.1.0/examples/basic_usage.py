#!/usr/bin/env python3
"""
Basic usage examples for deep-ocr package.

Installation:
    # Using uv (recommended)
    uv add deep-ocr

    # Using pip
    pip install deep-ocr
"""

from deep_ocr import DeepSeekOCR, OCRConfig


def basic_ocr_example():
    """Basic OCR example with default settings."""
    print("=== Basic OCR Example ===")

    # Initialize OCR with default settings
    ocr = DeepSeekOCR()

    # Process an image (replace with your image path)
    image_path = "sample_image.jpg"

    try:
        result = ocr.process(image_path, output_dir="basic_output")
        print(f"✓ OCR completed successfully!")
        print(f"Results saved to: basic_output/")

        # Access the extracted text
        if hasattr(result, "text"):
            print(f"Extracted text preview: {result.text[:100]}...")

    except FileNotFoundError:
        print(
            f"⚠️  Image file '{image_path}' not found. Please provide a valid image path."
        )
    except Exception as e:
        print(f"✗ Error: {e}")


def custom_config_example():
    """Example with custom configuration."""
    print("\n=== Custom Configuration Example ===")

    # Create custom configuration
    config = OCRConfig(
        model_size="large",  # Use large model for better accuracy
        device="cpu",  # Use CPU (change to "cuda:0" for GPU)
        save_results=True,  # Save results to files
        test_compress=False,  # Disable compression testing
    )

    # Initialize OCR with custom config
    ocr = DeepSeekOCR(config=config)

    # Process with custom prompt
    custom_prompt = "<image>\n<|grounding|>Extract all text from this document in a structured format."

    try:
        result = ocr.process(
            "sample_document.jpg", prompt=custom_prompt, output_dir="custom_output"
        )
        print(f"✓ Custom OCR completed successfully!")

    except FileNotFoundError:
        print(f"⚠️  Image file not found. Please provide a valid image path.")
    except Exception as e:
        print(f"✗ Error: {e}")


def markdown_conversion_example():
    """Example of converting document to markdown."""
    print("\n=== Markdown Conversion Example ===")

    ocr = DeepSeekOCR()

    try:
        # Convert document to markdown
        result = ocr.ocr_to_markdown(
            "sample_document.jpg", output_dir="markdown_output"
        )
        print(f"✓ Document converted to markdown!")
        print(f"Markdown file saved to: markdown_output/result.md")

    except FileNotFoundError:
        print(f"⚠️  Image file not found. Please provide a valid image path.")
    except Exception as e:
        print(f"✗ Error: {e}")


def text_extraction_example():
    """Example of plain text extraction."""
    print("\n=== Text Extraction Example ===")

    ocr = DeepSeekOCR()

    try:
        # Extract plain text
        result = ocr.ocr_to_text("sample_image.jpg", output_dir="text_output")
        print(f"✓ Text extracted successfully!")
        print(f"Text file saved to: text_output/result.txt")

    except FileNotFoundError:
        print(f"⚠️  Image file not found. Please provide a valid image path.")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    print("Deep-OCR Basic Usage Examples")
    print("=" * 40)

    # Run examples
    basic_ocr_example()
    custom_config_example()
    markdown_conversion_example()
    text_extraction_example()

    print("\n" + "=" * 40)
    print("Examples completed!")
    print(
        "\nNote: Replace 'sample_image.jpg' and 'sample_document.jpg' with actual image paths."
    )
