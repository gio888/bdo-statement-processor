"""Main processing logic for BDO Statement Processor."""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd

from .file_manager import FileManager
from .parser import BDOParser
import config


class BDOProcessor:
    """Main processor for BDO statement files."""
    
    def __init__(self, input_dir: str = None, dry_run: bool = False):
        """
        Initialize the processor.
        
        Args:
            input_dir: Directory containing BDO CSV files
            dry_run: If True, don't write output files
        """
        self.file_manager = FileManager(input_dir)
        self.parser = BDOParser()
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
        # Processing statistics
        self.stats = {
            'files_discovered': 0,
            'files_processed': 0,
            'files_failed': 0,
            'files_skipped': 0,
            'transactions_processed': 0,
            'backups_created': 0,
            'errors': []
        }
        
    def process_all(self, from_date: datetime = None) -> Dict:
        """
        Process all eligible BDO CSV files.
        
        Args:
            from_date: Minimum date to process files from
            
        Returns:
            Dictionary with processing statistics
        """
        self.logger.info("Starting BDO statement processing")
        
        # Discover files
        try:
            files = self.file_manager.discover_files(from_date)
            self.stats['files_discovered'] = len(files)
            
            if not files:
                self.logger.warning("No eligible files found")
                return self.stats
                
            # Log discovery summary
            file_stats = self.file_manager.get_file_stats(files)
            self.logger.info(f"Discovered {file_stats['total']} files: {file_stats['by_account']}")
            
            # Process each file
            for file_path, metadata in files:
                self._process_single_file(file_path, metadata)
                
        except Exception as e:
            self.logger.error(f"Error during file discovery: {e}")
            self.stats['errors'].append(f"File discovery error: {e}")
            
        # Log final statistics
        self._log_summary()
        return self.stats
        
    def _process_single_file(self, file_path: Path, metadata: dict) -> bool:
        """
        Process a single BDO CSV file.
        
        Args:
            file_path: Path to the CSV file
            metadata: File metadata dictionary
            
        Returns:
            True if processing was successful
        """
        self.logger.info(f"Processing file: {file_path.name}")
        
        try:
            # Parse the file
            transactions = self.parser.parse_file(file_path, metadata)
            
            if transactions is None or transactions.empty:
                self.logger.warning(f"No transactions found in {file_path.name}")
                self.stats['files_skipped'] += 1
                return False
                
            # Generate output path
            output_path = self.file_manager.generate_output_path(file_path, metadata)
            
            # Create backup if output file exists
            if output_path.exists():
                backup_path = self.file_manager.create_backup(output_path)
                if backup_path:
                    self.stats['backups_created'] += 1
                    
            # Write output file (unless dry run)
            if not self.dry_run:
                success = self._write_output_file(transactions, output_path)
                if not success:
                    self.stats['files_failed'] += 1
                    return False
            else:
                self.logger.info(f"DRY RUN: Would write {len(transactions)} transactions to {output_path.name}")
                
            # Update statistics
            self.stats['files_processed'] += 1
            self.stats['transactions_processed'] += len(transactions)
            
            self.logger.info(f"Successfully processed {len(transactions)} transactions from {file_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path.name}: {e}")
            self.stats['files_failed'] += 1
            self.stats['errors'].append(f"{file_path.name}: {e}")
            return False
            
    def _write_output_file(self, transactions: pd.DataFrame, output_path: Path) -> bool:
        """
        Write transactions to output CSV file.
        
        Args:
            transactions: DataFrame with transaction data
            output_path: Path for output file
            
        Returns:
            True if writing was successful
        """
        try:
            # Validate data before writing
            validation_errors = self._validate_transactions(transactions)
            if validation_errors:
                self.logger.warning(f"Validation errors for {output_path.name}: {validation_errors}")
                
            # Write to CSV
            transactions.to_csv(output_path, index=False)
            self.logger.info(f"Wrote output file: {output_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing output file {output_path.name}: {e}")
            return False
            
    def _validate_transactions(self, transactions: pd.DataFrame) -> List[str]:
        """
        Validate transaction data.
        
        Args:
            transactions: DataFrame with transaction data
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check required columns
        required_columns = ['Date', 'Description', 'Debit', 'Credit', 'Account', 'Transfer Account']
        missing_columns = [col for col in required_columns if col not in transactions.columns]
        if missing_columns:
            errors.append(f"Missing columns: {missing_columns}")
            
        # Check for empty dates
        if transactions['Date'].isna().any():
            errors.append("Found transactions with missing dates")
            
        # Check for transactions without amounts
        no_amount_count = ((transactions['Debit'] == '') & (transactions['Credit'] == '')).sum()
        if no_amount_count > 0:
            errors.append(f"Found {no_amount_count} transactions without debit or credit amounts")
            
        # Check date format
        invalid_dates = []
        for idx, date_str in transactions['Date'].items():
            if pd.notna(date_str):
                try:
                    datetime.strptime(str(date_str), '%Y-%m-%d')
                except ValueError:
                    invalid_dates.append(str(date_str))
                    
        if invalid_dates:
            errors.append(f"Invalid date formats: {invalid_dates[:5]}")  # Show first 5
            
        return errors
        
    def _log_summary(self):
        """Log processing summary."""
        self.logger.info("=== PROCESSING SUMMARY ===")
        self.logger.info(f"Files discovered: {self.stats['files_discovered']}")
        self.logger.info(f"Files processed: {self.stats['files_processed']}")
        self.logger.info(f"Files failed: {self.stats['files_failed']}")
        self.logger.info(f"Files skipped: {self.stats['files_skipped']}")
        self.logger.info(f"Transactions processed: {self.stats['transactions_processed']}")
        self.logger.info(f"Backups created: {self.stats['backups_created']}")
        
        if self.stats['errors']:
            self.logger.warning(f"Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                self.logger.warning(f"  - {error}")
                
    def get_processing_report(self) -> str:
        """
        Generate a formatted processing report.
        
        Returns:
            Formatted report string
        """
        report = []
        report.append("BDO Statement Processing Report")
        report.append("=" * 40)
        report.append(f"Files discovered: {self.stats['files_discovered']}")
        report.append(f"Files processed: {self.stats['files_processed']}")
        report.append(f"Files failed: {self.stats['files_failed']}")
        report.append(f"Files skipped: {self.stats['files_skipped']}")
        report.append(f"Transactions processed: {self.stats['transactions_processed']}")
        report.append(f"Backups created: {self.stats['backups_created']}")
        
        if self.stats['errors']:
            report.append(f"\nErrors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                report.append(f"  - {error}")
                
        return "\n".join(report)
        
    def process_file_list(self, file_paths: List[Path]) -> Dict:
        """
        Process a specific list of files.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dictionary with processing statistics
        """
        self.logger.info(f"Processing {len(file_paths)} specific files")
        
        for file_path in file_paths:
            try:
                # Extract metadata from filename
                import re
                pattern = re.compile(config.FILE_PATTERN)
                metadata = self.file_manager._extract_metadata(
                    file_path, 
                    pattern
                )
                
                if metadata:
                    self._process_single_file(file_path, metadata)
                    self.stats['files_discovered'] += 1
                else:
                    self.logger.warning(f"Could not extract metadata from {file_path.name}")
                    self.stats['files_skipped'] += 1
                    
            except Exception as e:
                self.logger.error(f"Error processing {file_path.name}: {e}")
                self.stats['files_failed'] += 1
                self.stats['errors'].append(f"{file_path.name}: {e}")
                
        self._log_summary()
        return self.stats