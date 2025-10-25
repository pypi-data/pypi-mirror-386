#!/usr/bin/env python3
"""
Command-line interface for DeepSeek-OCR.
"""

import argparse
import sys
from pathlib import Path
from . import DeepSeekOCR, OCRConfig


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DeepSeek-OCR: A production-ready wrapper for DeepSeek-OCR inference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  deep-ocr image.jpg                           # Basic OCR
  deep-ocr image.jpg -o output/                # Specify output directory
  deep-ocr image.jpg --model-size large        # Use large model
  deep-ocr image.jpg --prompt "Extract text"   # Custom prompt
  deep-ocr image.jpg --device cuda:0 --flash-attention  # GPU with Flash Attention
        """,
    )

    parser.add_argument("image", help="Path to the image file to process")

    parser.add_argument(
        "-o",
        "--output",
        default="output",
        help="Output directory for results (default: output)",
    )

    parser.add_argument(
        "--model-size",
        choices=["tiny", "small", "base", "large", "gundam"],
        default="tiny",
        help="Model size preset (default: tiny)",
    )

    parser.add_argument("--device", default="cpu", help="Device to use (default: cpu)")

    parser.add_argument(
        "--prompt",
        default="<image>\n<|grounding|>Convert the document to markdown format.",
        help="Custom prompt for OCR",
    )

    parser.add_argument(
        "--save-results",
        action="store_true",
        default=True,
        help="Save results to files (default: True)",
    )

    parser.add_argument(
        "--no-save-results", action="store_true", help="Don't save results to files"
    )

    parser.add_argument(
        "--test-compress", action="store_true", help="Test compression mode"
    )

    parser.add_argument("--crop-mode", action="store_true", help="Enable crop mode")

    parser.add_argument(
        "--flash-attention",
        action="store_true",
        help="Enable Flash Attention 2 for GPU (requires flash-attn)",
    )

    args = parser.parse_args()

    # Validate input file
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Error: Image file '{args.image}' not found.", file=sys.stderr)
        sys.exit(1)

    # Create configuration
    config = OCRConfig(
        model_size=args.model_size,
        device=args.device,
        save_results=args.save_results and not args.no_save_results,
        test_compress=args.test_compress,
        crop_mode=args.crop_mode,
        use_flash_attention=args.flash_attention,
    )

    try:
        # Initialize OCR
        print(f"Initializing DeepSeek-OCR with {args.model_size} model...")
        ocr = DeepSeekOCR(config=config)

        # Process image
        print(f"Processing: {image_path.name}")
        result = ocr.process(
            str(image_path), prompt=args.prompt, output_dir=args.output
        )

        print(f"✓ Processing complete! Results saved to: {args.output}")

        # Print result summary
        if hasattr(result, "text") and result.text:
            print(f"\nExtracted text preview:")
            print("-" * 50)
            print(result.text[:200] + "..." if len(result.text) > 200 else result.text)
            print("-" * 50)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
