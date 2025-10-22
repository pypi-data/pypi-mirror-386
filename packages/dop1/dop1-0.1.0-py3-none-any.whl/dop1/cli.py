"""
Command line interface for DOP1 package.
"""

import argparse
import sys
import os
from pathlib import Path
from .predictor import DOPPredictor
from .exceptions import DOPError


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DOP1 - Diabetes Osteoporosis Prediction Package",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single CSV file
  dop1 predict data.csv --output results/
  
  # Process with custom API key
  dop1 predict data.csv --api-key your-key --output results/
  
  # Process with custom model
  dop1 predict data.csv --model gpt-4 --output results/
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Predict osteoporosis risk for patients')
    predict_parser.add_argument('input_file', help='Input CSV file with patient data')
    predict_parser.add_argument('--output', '-o', default='results', 
                               help='Output directory for results (default: results)')
    predict_parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    predict_parser.add_argument('--base-url', default='https://api.ocoolai.com/v1',
                               help='API base URL (default: https://api.ocoolai.com/v1)')
    predict_parser.add_argument('--model', default='gpt-5',
                               help='Model to use for predictions (default: gpt-5)')
    predict_parser.add_argument('--no-skip', action='store_true',
                               help='Do not skip existing result files')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show model information')
    info_parser.add_argument('--api-key', help='OpenAI API key (or set OPENAI_API_KEY env var)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'predict':
            run_predict(args)
        elif args.command == 'info':
            run_info(args)
    except DOPError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


def run_predict(args):
    """Run prediction command."""
    # Validate input file
    if not os.path.exists(args.input_file):
        raise DOPError(f"Input file not found: {args.input_file}")
    
    # Initialize predictor
    predictor = DOPPredictor(
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model
    )
    
    print(f"Processing file: {args.input_file}")
    print(f"Output directory: {args.output}")
    print(f"Model: {args.model}")
    print(f"Skip existing files: {not args.no_skip}")
    print()
    
    # Process batch
    predictor.process_batch(
        filepath=args.input_file,
        output_dir=args.output,
        skip_existing=not args.no_skip
    )
    
    print(f"\nProcessing completed! Results saved to: {args.output}")


def run_info(args):
    """Run info command."""
    predictor = DOPPredictor(api_key=args.api_key)
    info = predictor.get_model_info()
    
    print("DOP1 Model Information")
    print("=" * 30)
    for key, value in info.items():
        print(f"{key.replace('_', ' ').title()}: {value}")


if __name__ == '__main__':
    main()
