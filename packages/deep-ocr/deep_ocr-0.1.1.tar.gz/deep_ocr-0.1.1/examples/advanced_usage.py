#!/usr/bin/env python3
"""
Advanced usage examples for deep-ocr package including batch processing and Flash Attention.

Installation:
    # Using uv (recommended)
    uv add "deep-ocr[flash-attn]"

    # Using pip
    pip install deep-ocr[flash-attn]
"""

from deep_ocr import DeepSeekOCR, OCRConfig


def flash_attention_example():
    """Example using Flash Attention for high performance on GPU."""
    print("=== Flash Attention Example ===")

    # Check if CUDA is available
    import torch

    if not torch.cuda.is_available():
        print("⚠️  CUDA not available. Flash Attention requires GPU.")
        print("   This example will run with standard attention.")
        device = "cpu"
        use_flash_attention = False
    else:
        print("⚡ CUDA available! Using Flash Attention for high performance.")
        device = "cuda:0"
        use_flash_attention = True

    # Create configuration with Flash Attention
    config = OCRConfig(
        model_size="large",
        device=device,
        use_flash_attention=use_flash_attention,
        save_results=True,
    )

    # Initialize OCR
    ocr = DeepSeekOCR(config=config)

    try:
        result = ocr.process("sample_image.jpg", output_dir="flash_output")
        print(f"✓ High-performance OCR completed!")

    except FileNotFoundError:
        print(f"⚠️  Image file not found. Please provide a valid image path.")
    except Exception as e:
        print(f"✗ Error: {e}")


def batch_processing_example():
    """Example of batch processing multiple images with the same prompt."""
    print("\n=== Batch Processing Example ===")

    ocr = DeepSeekOCR()

    # List of images to process
    images = ["document1.jpg", "document2.jpg", "document3.jpg"]

    # Common prompt for all images
    prompt = "<image>\n<|grounding|>Extract all text from this document."

    try:
        results = ocr.batch_process(images, output_dir="batch_output", prompt=prompt)

        print(f"✓ Batch processing completed!")
        print(f"Processed {len(results)} images:")

        for i, result in enumerate(results, 1):
            if result["status"] == "success":
                print(f"  [{i}] ✓ {result['image']} - Success")
            else:
                print(f"  [{i}] ✗ {result['image']} - Error: {result['error']}")

    except Exception as e:
        print(f"✗ Error: {e}")


def batch_processing_with_separate_prompts_example():
    """Example of batch processing with different prompts for each image."""
    print("\n=== Batch Processing with Separate Prompts Example ===")

    ocr = DeepSeekOCR()

    # Define image-prompt pairs
    image_prompt_pairs = [
        # Using tuple format
        (
            "receipt.jpg",
            "<image>\n<|grounding|>Extract all items and prices from this receipt.",
        ),
        (
            "invoice.jpg",
            "<image>\n<|grounding|>Extract company name, invoice number, and total amount.",
        ),
        (
            "document.jpg",
            "<image>\n<|grounding|>Convert this document to markdown format.",
        ),
        # Using dictionary format
        {
            "image": "id_card.jpg",
            "prompt": "<image>\n<|grounding|>Extract name, ID number, and date of birth.",
        },
        {
            "image": "business_card.jpg",
            "prompt": "<image>\n<|grounding|>Extract name, company, phone, and email.",
        },
    ]

    try:
        results = ocr.batch_process_with_prompts(
            image_prompt_pairs, "batch_separate_output"
        )

        print(f"✓ Batch processing with separate prompts completed!")
        print(f"Processed {len(results)} images:")

        for i, result in enumerate(results, 1):
            if result["status"] == "success":
                print(f"  [{i}] ✓ {result['image']} - Success")
                print(f"      Prompt: {result['prompt'][:50]}...")
            else:
                print(f"  [{i}] ✗ {result['image']} - Error: {result['error']}")

    except Exception as e:
        print(f"✗ Error: {e}")


def different_model_sizes_example():
    """Example showing different model sizes and their trade-offs."""
    print("\n=== Different Model Sizes Example ===")

    model_sizes = ["tiny", "small", "base", "large", "gundam"]

    for size in model_sizes:
        print(f"\n--- Testing {size.upper()} model ---")

        config = OCRConfig(
            model_size=size,
            device="cpu",  # Use CPU for consistent comparison
            save_results=False,  # Don't save for this demo
        )

        try:
            ocr = DeepSeekOCR(config=config)
            print(f"✓ {size.upper()} model loaded successfully")
            print(f"  Base size: {config.base_size}")
            print(f"  Image size: {config.image_size}")
            print(f"  Crop mode: {config.crop_mode}")

        except Exception as e:
            print(f"✗ Error loading {size} model: {e}")


def performance_comparison_example():
    """Example comparing performance with and without Flash Attention."""
    print("\n=== Performance Comparison Example ===")

    import time
    import torch

    if not torch.cuda.is_available():
        print("⚠️  CUDA not available. Skipping performance comparison.")
        return

    image_path = "sample_image.jpg"

    # Test without Flash Attention
    print("Testing without Flash Attention...")
    config_no_flash = OCRConfig(
        model_size="base", device="cuda:0", use_flash_attention=False
    )

    try:
        ocr_no_flash = DeepSeekOCR(config_no_flash)

        start_time = time.time()
        result_no_flash = ocr_no_flash.process(image_path, output_dir="perf_no_flash")
        time_no_flash = time.time() - start_time

        print(f"✓ Without Flash Attention: {time_no_flash:.2f} seconds")

    except Exception as e:
        print(f"✗ Error without Flash Attention: {e}")
        time_no_flash = None

    # Test with Flash Attention
    print("Testing with Flash Attention...")
    config_flash = OCRConfig(
        model_size="base", device="cuda:0", use_flash_attention=True
    )

    try:
        ocr_flash = DeepSeekOCR(config_flash)

        start_time = time.time()
        result_flash = ocr_flash.process(image_path, output_dir="perf_flash")
        time_flash = time.time() - start_time

        print(f"✓ With Flash Attention: {time_flash:.2f} seconds")

        if time_no_flash:
            speedup = time_no_flash / time_flash
            print(f"⚡ Speedup: {speedup:.2f}x faster with Flash Attention!")

    except Exception as e:
        print(f"✗ Error with Flash Attention: {e}")


if __name__ == "__main__":
    print("Deep-OCR Advanced Usage Examples")
    print("=" * 50)

    # Run examples
    flash_attention_example()
    batch_processing_example()
    batch_processing_with_separate_prompts_example()
    different_model_sizes_example()
    performance_comparison_example()

    print("\n" + "=" * 50)
    print("Advanced examples completed!")
    print("\nNote: Replace image filenames with actual image paths.")
    print("For Flash Attention examples, ensure you have:")
    print("  - NVIDIA GPU with CUDA support")
    print("  - flash-attn installed: pip install flash-attn")
