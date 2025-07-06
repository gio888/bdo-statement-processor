"""Monthly processing workflow for BDO Statement Processor."""

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
import calendar

from .file_manager import FileManager
from .parser import BDOParser
import config


class MonthlyProcessor:
    """Handles monthly processing workflow for production use."""
    
    def __init__(self, input_dir: str = None, dry_run: bool = False):
        """
        Initialize the monthly processor.
        
        Args:
            input_dir: Directory containing BDO CSV files
            dry_run: If True, don't write output files
        """
        self.file_manager = FileManager(input_dir)
        self.parser = BDOParser()
        self.dry_run = dry_run
        self.logger = logging.getLogger(__name__)
        
        # Monthly processing statistics
        self.stats = {
            'new_files_found': 0,
            'files_processed': 0,
            'files_failed': 0,
            'missing_accounts': [],
            'transactions_processed': 0,
            'target_month': None,
            'output_file': None,
            'errors': []
        }
        
    def process_monthly(self, target_month: str = None) -> Dict:
        """
        Process unprocessed files for monthly workflow.
        
        Args:
            target_month: Target month in YYYY-MM format (auto-detected if None)
            
        Returns:
            Dictionary with processing statistics
        """
        self.logger.info("Starting monthly BDO statement processing")
        
        # Discover unprocessed months
        unprocessed_months = self._discover_unprocessed_months()
        
        if not unprocessed_months:
            print("✅ No unprocessed months found!")
            return self.stats
        
        # Display unprocessed months
        sorted_months = sorted(unprocessed_months.keys())
        print(f"\n📅 Found {len(sorted_months)} unprocessed months:")
        for month in sorted_months:
            files = unprocessed_months[month]
            account_types = {metadata['account_type'] for _, metadata in files}
            account_info = " + ".join(sorted(account_types))
            print(f"   - {month} ({len(files)} files: {account_info})")
        
        # Process all months chronologically
        total_processed = 0
        for month in sorted_months:
            month_files = unprocessed_months[month]
            print(f"\n🔄 Processing {month}...")
            
            # Check for missing accounts
            self._check_missing_accounts(month_files, month)
            
            # Process files and combine
            combined_transactions = self._process_and_combine_files(month_files)
            
            if combined_transactions is None or combined_transactions.empty:
                print(f"❌ No transactions found for {month}")
                continue
                
            # Generate output file
            output_path = self._generate_monthly_output_path(month)
            
            if not self.dry_run:
                success = self._write_monthly_output(combined_transactions, output_path)
                if success:
                    print(f"✅ Created: {output_path.name}")
                    total_processed += 1
            else:
                print(f"DRY RUN: Would write {len(combined_transactions)} transactions to {output_path.name}")
                total_processed += 1
        
        # Update stats
        self.stats['months_processed'] = total_processed
        self.stats['total_months_found'] = len(sorted_months)
        
        print(f"\n📊 SUMMARY: Processed {total_processed} of {len(sorted_months)} months")
        self._log_monthly_summary()
        return self.stats
        
    def _discover_unprocessed_months(self) -> Dict[str, List[Tuple[Path, dict]]]:
        """Discover months that haven't been processed yet."""
        all_files = self.file_manager.discover_files()
        
        # Group files by month
        files_by_month = {}
        for file_path, metadata in all_files:
            month_key = metadata['date'].strftime('%Y-%m')
            if month_key not in files_by_month:
                files_by_month[month_key] = []
            files_by_month[month_key].append((file_path, metadata))
        
        # Find unprocessed months
        unprocessed_months = {}
        for month, files in files_by_month.items():
            if not self._is_month_processed(month):
                unprocessed_months[month] = files
                
        self.logger.info(f"Found {len(unprocessed_months)} unprocessed months")
        return unprocessed_months
    
    def _is_month_processed(self, target_month: str) -> bool:
        """Check if a month has already been processed."""
        monthly_output = self.file_manager.input_dir / f"for_import_My_Transactions BDO {target_month}.csv"
        return monthly_output.exists()
        
    def _detect_month_from_files(self, files: List[Tuple[Path, dict]]) -> Optional[str]:
        """Detect the target month from file dates."""
        if not files:
            return None
            
        # Get the most common month from files
        months = []
        for _, metadata in files:
            file_date = metadata['date']
            month_str = file_date.strftime('%Y-%m')
            months.append(month_str)
            
        if months:
            # Return the most common month
            most_common = max(set(months), key=months.count)
            return most_common
            
        return None
        
    def _confirm_month(self, detected_month: str) -> bool:
        """Ask user to confirm the detected month."""
        month_name = datetime.strptime(detected_month, '%Y-%m').strftime('%B %Y')
        response = input(f"\n📅 Processing files for {month_name}, correct? (Y/n): ").strip().lower()
        return response in ['', 'y', 'yes']
        
    def _get_user_month(self) -> str:
        """Get target month from user input."""
        while True:
            month_input = input("Enter target month (YYYY-MM): ").strip()
            try:
                # Validate format
                datetime.strptime(month_input, '%Y-%m')
                return month_input
            except ValueError:
                print("Invalid format. Please use YYYY-MM (e.g., 2024-03)")
                
    def _filter_files_by_month(self, files: List[Tuple[Path, dict]], target_month: str) -> List[Tuple[Path, dict]]:
        """Filter files to only include those from target month."""
        target_date = datetime.strptime(target_month, '%Y-%m')
        month_files = []
        
        for file_path, metadata in files:
            file_date = metadata['date']
            if file_date.year == target_date.year and file_date.month == target_date.month:
                month_files.append((file_path, metadata))
                
        return month_files
        
    def _check_missing_accounts(self, files: List[Tuple[Path, dict]], target_month: str):
        """Check if both account types are present."""
        account_types = {metadata['account_type'] for _, metadata in files}
        expected_accounts = {'Checking', 'Savings'}
        missing = expected_accounts - account_types
        
        if missing:
            self.stats['missing_accounts'] = list(missing)
            month_name = datetime.strptime(target_month, '%Y-%m').strftime('%B %Y')
            print(f"⚠️  WARNING: Missing {', '.join(missing)} account data for {month_name}")
            print("   Processing will continue with available data")
            
    def _process_and_combine_files(self, files: List[Tuple[Path, dict]]) -> Optional[pd.DataFrame]:
        """Process files and combine transactions."""
        all_transactions = []
        
        for file_path, metadata in files:
            self.logger.info(f"Processing file: {file_path.name}")
            
            try:
                # Parse the file with original date format
                transactions = self._parse_file_keep_date_format(file_path, metadata)
                
                if transactions is not None and not transactions.empty:
                    all_transactions.append(transactions)
                    self.stats['files_processed'] += 1
                    self.stats['transactions_processed'] += len(transactions)
                    print(f"✅ Processed {len(transactions)} transactions from {file_path.name}")
                else:
                    print(f"⚠️  No transactions found in {file_path.name}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {file_path.name}: {e}")
                self.stats['files_failed'] += 1
                self.stats['errors'].append(f"{file_path.name}: {e}")
                print(f"❌ Failed to process {file_path.name}: {e}")
                
        if not all_transactions:
            return None
            
        # Combine all transactions
        combined_df = pd.concat(all_transactions, ignore_index=True)
        
        # Sort by date chronologically
        combined_df['_sort_date'] = pd.to_datetime(combined_df['Date'], format='%m/%d/%Y')
        combined_df = combined_df.sort_values('_sort_date')
        combined_df = combined_df.drop('_sort_date', axis=1)
        
        return combined_df
        
    def _parse_file_keep_date_format(self, file_path: Path, metadata: dict) -> Optional[pd.DataFrame]:
        """Parse file but keep original M/D/YYYY date format."""
        # Use existing parser but modify date format
        transactions = self.parser.parse_file(file_path, metadata)
        
        if transactions is None or transactions.empty:
            return None
            
        # Convert date back to M/D/YYYY format
        transactions['Date'] = pd.to_datetime(transactions['Date']).dt.strftime('%-m/%-d/%Y')
        
        return transactions
        
    def _generate_monthly_output_path(self, target_month: str) -> Path:
        """Generate output file path for monthly combined file."""
        filename = f"for_import_My_Transactions BDO {target_month}.csv"
        return self.file_manager.input_dir / filename
        
    def _write_monthly_output(self, transactions: pd.DataFrame, output_path: Path) -> bool:
        """Write monthly combined output file."""
        try:
            # Ensure proper column order
            columns = ['Date', 'Description', 'Debit', 'Credit', 'Account', 'Transfer Account']
            transactions = transactions[columns]
            
            transactions.to_csv(output_path, index=False)
            print(f"✅ Created monthly output: {output_path.name}")
            self.logger.info(f"Wrote monthly output file: {output_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing monthly output file {output_path.name}: {e}")
            print(f"❌ Error writing output file: {e}")
            return False
            
    def _log_monthly_summary(self):
        """Log monthly processing summary."""
        months_processed = self.stats.get('months_processed', 0)
        total_months = self.stats.get('total_months_found', 0)
        
        self.logger.info(f"Monthly processing completed: {months_processed}/{total_months} months processed")
        self.logger.info(f"Total files processed: {self.stats['files_processed']}")
        self.logger.info(f"Total transactions processed: {self.stats['transactions_processed']}")
        
        if self.stats['errors']:
            self.logger.error(f"Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                self.logger.error(f"  - {error}")