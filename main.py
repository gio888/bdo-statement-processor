#!/usr/bin/env python3
"""
BDO Statement Processor - Main Entry Point

Process BDO bank statement CSV files and prepare them for accounting software import.
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.processor import BDOProcessor
from src.utils import setup_logging, validate_date_string, validate_directory_path
import config


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Process BDO bank statement CSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --monthly                         # Monthly workflow (production)
  python main.py                                   # Process all files with default settings
  python main.py --input-dir "/path/to/files"      # Use custom input directory
  python main.py --from-date "2024-03-01"          # Process files from specific date
  python main.py --dry-run                         # Show what would be processed
  python main.py --log-level DEBUG                 # Enable debug logging
        """
    )
    
    parser.add_argument(
        '--monthly',
        action='store_true',
        help='Run monthly workflow (detects new files, combines into single output)'
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        default=config.DEFAULT_INPUT_DIR,
        help=f'Input directory containing BDO CSV files (default: {config.DEFAULT_INPUT_DIR})'
    )
    
    parser.add_argument(
        '--from-date',
        type=str,
        default=config.MIN_PROCESS_DATE.strftime('%Y-%m-%d'),
        help=f'Process files from this date onwards (default: {config.MIN_PROCESS_DATE.strftime("%Y-%m-%d")})'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=config.DEFAULT_DRY_RUN,
        help='Show what would be processed without writing files'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default=config.DEFAULT_LOG_LEVEL,
        help=f'Set logging level (default: {config.DEFAULT_LOG_LEVEL})'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Custom log file path (default: logs/bdo_processor.log)'
    )
    
    parser.add_argument(
        '--files',
        nargs='+',
        type=str,
        help='Process specific files instead of scanning directory'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='BDO Statement Processor 1.0.0'
    )
    
    return parser.parse_args()


def validate_arguments(args):
    """Validate command line arguments."""
    errors = []
    
    # Validate input directory
    try:
        validate_directory_path(args.input_dir)
    except (FileNotFoundError, ValueError) as e:
        errors.append(f"Input directory error: {e}")
    
    # Validate from_date
    try:
        validate_date_string(args.from_date)
    except ValueError as e:
        errors.append(f"From date error: {e}")
    
    # Validate specific files if provided
    if args.files:
        for file_path in args.files:
            path = Path(file_path)
            if not path.exists():
                errors.append(f"File not found: {file_path}")
            elif not path.is_file():
                errors.append(f"Not a file: {file_path}")
    
    return errors


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Validate arguments
    validation_errors = validate_arguments(args)
    if validation_errors:
        print("Validation errors:")
        for error in validation_errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Setup logging
    try:
        logger = setup_logging(args.log_level, args.log_file)
    except Exception as e:
        print(f"Error setting up logging: {e}")
        sys.exit(1)
    
    # Log startup information
    logger.info("=" * 50)
    if args.monthly:
        logger.info("BDO Statement Processor - Monthly Workflow")
    else:
        logger.info("BDO Statement Processor Starting")
    logger.info("=" * 50)
    logger.info(f"Input directory: {args.input_dir}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info(f"Log level: {args.log_level}")
    
    try:
        # Monthly workflow
        if args.monthly:
            from src.monthly_processor import MonthlyProcessor
            processor = MonthlyProcessor(
                input_dir=args.input_dir,
                dry_run=args.dry_run
            )
            stats = processor.process_monthly()
        else:
            # Regular workflow
            logger.info(f"From date: {args.from_date}")
            
            # Parse from_date
            from_date = validate_date_string(args.from_date)
            
            # Create processor
            processor = BDOProcessor(
                input_dir=args.input_dir,
                dry_run=args.dry_run
            )
        
            # Process files for regular workflow
            if args.files:
                # Process specific files
                file_paths = [Path(f) for f in args.files]
                logger.info(f"Processing {len(file_paths)} specific files")
                stats = processor.process_file_list(file_paths)
            else:
                # Process all eligible files
                logger.info("Processing all eligible files")
                stats = processor.process_all(from_date)
            
            # Generate and display report
            report = processor.get_processing_report()
            print("\n" + report)
        
        # Exit with appropriate code
        if stats['files_failed'] > 0:
            logger.warning("Some files failed to process")
            sys.exit(1)
        elif stats['files_processed'] == 0:
            logger.warning("No files were processed")
            sys.exit(1)
        else:
            logger.info("Processing completed successfully")
            sys.exit(0)
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()