"""CSV parsing utilities for BDO Statement Processor."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
from difflib import get_close_matches

import config


class BDOParser:
    """Parser for BDO CSV statement files."""
    
    def __init__(self):
        """Initialize the parser."""
        self.logger = logging.getLogger(__name__)
        
    def parse_file(self, file_path: Path, metadata: dict) -> Optional[pd.DataFrame]:
        """
        Parse a BDO CSV file and extract transaction data.
        
        Args:
            file_path: Path to the CSV file
            metadata: File metadata dictionary
            
        Returns:
            DataFrame with cleaned transaction data, or None if parsing fails
        """
        try:
            # Read the file with error handling
            df = self._read_csv_file(file_path)
            if df is None:
                return None
                
            # Find the header row dynamically
            header_row = self._find_header_row(df)
            if header_row is None:
                self.logger.error(f"Could not find header row in {file_path.name}")
                return None
                
            # Extract transaction data
            transactions = self._extract_transactions(df, header_row, metadata)
            if transactions is None or transactions.empty:
                self.logger.warning(f"No transactions found in {file_path.name}")
                return None
                
            # Clean and validate the data
            cleaned_transactions = self._clean_data(transactions)
            
            self.logger.info(f"Successfully parsed {len(cleaned_transactions)} transactions from {file_path.name}")
            return cleaned_transactions
            
        except Exception as e:
            self.logger.error(f"Error parsing file {file_path.name}: {e}")
            return None
            
    def _read_csv_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Read CSV file with various encoding attempts."""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding, header=None, dtype=str)
                self.logger.debug(f"Successfully read {file_path.name} with encoding: {encoding}")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.logger.error(f"Error reading {file_path.name}: {e}")
                return None
                
        self.logger.error(f"Could not read {file_path.name} with any encoding")
        return None
        
    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """Find the row containing the transaction headers."""
        target_columns = set(config.EXPECTED_COLUMNS)
        
        for idx, row in df.iterrows():
            # Convert row to string and check for header markers
            row_str = ' '.join(str(cell) for cell in row if pd.notna(cell))
            
            # Look for "Posting Date" as the key indicator
            if 'Posting Date' in row_str:
                return idx
                
            # Also check for fuzzy matches
            row_columns = [str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip()]
            if len(row_columns) >= 4:  # Should have at least 4 columns
                matches = sum(1 for col in row_columns if self._fuzzy_match_column(col))
                if matches >= 3:  # Need at least 3 column matches
                    return idx
                    
        return None
        
    def _fuzzy_match_column(self, column_name: str) -> bool:
        """Check if a column name matches expected columns using fuzzy matching."""
        column_name = column_name.strip()
        
        # Direct match
        if column_name in config.EXPECTED_COLUMNS:
            return True
            
        # Check alternatives
        for expected_col, alternatives in config.COLUMN_ALTERNATIVES.items():
            if column_name in alternatives:
                return True
                
        # Fuzzy matching
        close_matches = get_close_matches(column_name, config.EXPECTED_COLUMNS, n=1, cutoff=0.8)
        return len(close_matches) > 0
        
    def _extract_transactions(self, df: pd.DataFrame, header_row: int, metadata: dict) -> Optional[pd.DataFrame]:
        """Extract transaction data from the DataFrame."""
        # Set the header row - handle duplicate column names
        header_values = df.iloc[header_row].tolist()
        unique_columns = []
        for i, col in enumerate(header_values):
            if pd.isna(col) or str(col).strip() == '':
                unique_columns.append(f'empty_col_{i}')
            else:
                unique_columns.append(str(col).strip())
        
        # Make column names unique by adding suffixes
        seen = {}
        final_columns = []
        for col in unique_columns:
            if col in seen:
                seen[col] += 1
                final_columns.append(f"{col}_{seen[col]}")
            else:
                seen[col] = 0
                final_columns.append(col)
        
        df.columns = final_columns
        transaction_df = df.iloc[header_row + 1:].copy()
        
        # Detect format and process accordingly
        if self._is_new_format(transaction_df.columns):
            self.logger.info("Detected new CSV format (2025-03 onwards)")
            output_df = self._process_new_format(transaction_df)
        else:
            self.logger.info("Detected legacy CSV format (pre-2025-03)")
            output_df = self._process_legacy_format(transaction_df)
            
        if output_df is None:
            return None
        
        # Add account information
        account_type = metadata['account_type']
        output_df['Account'] = config.ACCOUNT_MAPPINGS.get(account_type, f"Unknown:{account_type}")
        
        # Set Transfer Account based on transaction type
        output_df['Transfer Account'] = output_df['Description'].apply(self._map_transfer_account)
        
        return output_df
        
    def _map_columns(self, columns: List[str]) -> Dict[str, str]:
        """Map actual column names to expected column names."""
        column_mapping = {}
        
        for actual_col in columns:
            if pd.isna(actual_col):
                continue
                
            actual_col = str(actual_col).strip()
            
            # Direct match
            if actual_col in config.EXPECTED_COLUMNS:
                column_mapping[actual_col] = actual_col
                continue
                
            # Check alternatives
            found_match = False
            for expected_col, alternatives in config.COLUMN_ALTERNATIVES.items():
                if actual_col in alternatives:
                    column_mapping[expected_col] = actual_col
                    found_match = True
                    break
                    
            if found_match:
                continue
                
            # Fuzzy matching
            close_matches = get_close_matches(actual_col, config.EXPECTED_COLUMNS, n=1, cutoff=0.8)
            if close_matches:
                column_mapping[close_matches[0]] = actual_col
                
        return column_mapping
        
    def _filter_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filter out non-transaction rows."""
        filtered_rows = []
        
        for idx, row in df.iterrows():
            row_str = ' '.join(str(cell) for cell in row if pd.notna(cell))
            
            # Check for end markers
            if any(marker in row_str for marker in config.END_OF_REPORT_MARKERS):
                break
                
            # Check if row has transaction data (has date and description)
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip():
                # Basic validation: first column should look like a date
                first_col = str(row.iloc[0]).strip()
                if self._looks_like_date(first_col):
                    filtered_rows.append(row)
                    
        return pd.DataFrame(filtered_rows)
        
    def _looks_like_date(self, text: str) -> bool:
        """Check if text looks like a date."""
        # Common date patterns
        date_patterns = [
            r'\w{3}\s+\d{1,2},\s+\d{4}',  # "Feb 29, 2024"
            r'\d{1,2}/\d{1,2}/\d{4}',     # "02/29/2024"
            r'\d{4}-\d{2}-\d{2}',         # "2024-02-29"
        ]
        
        for pattern in date_patterns:
            if re.search(pattern, text):
                return True
                
        return False
        
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate the extracted data."""
        cleaned_df = df.copy()
        
        # Check if data is already in final format (from new format processing)
        expected_final_columns = ['Date', 'Description', 'Debit', 'Credit', 'Account', 'Transfer Account']
        if all(col in cleaned_df.columns for col in expected_final_columns[:4]):
            # Data is already cleaned, just ensure proper column order
            final_columns = ['Date', 'Description', 'Debit', 'Credit', 'Account', 'Transfer Account']
            cleaned_df = cleaned_df[final_columns]
        else:
            # Legacy format processing
            # Clean date column
            cleaned_df['Date'] = cleaned_df['Posting Date'].apply(self._clean_date)
            
            # Clean description
            cleaned_df['Description'] = cleaned_df['Description'].apply(self._clean_description)
            
            # Clean monetary amounts
            cleaned_df['Debit'] = cleaned_df['Debit Amount'].apply(self._clean_amount)
            cleaned_df['Credit'] = cleaned_df['Credit Amount'].apply(self._clean_amount)
            
            # Select final columns
            final_columns = ['Date', 'Description', 'Debit', 'Credit', 'Account', 'Transfer Account']
            cleaned_df = cleaned_df[final_columns]
        
        # Remove rows with invalid dates
        cleaned_df = cleaned_df[cleaned_df['Date'].notna()]
        
        return cleaned_df
        
    def _clean_date(self, date_str: str) -> Optional[str]:
        """Clean and convert date string to YYYY-MM-DD format."""
        if pd.isna(date_str):
            return None
            
        date_str = str(date_str).strip()
        
        # Try different date formats
        formats = [
            '%b %d, %Y',    # "Feb 29, 2024"
            '%m/%d/%Y',     # "02/29/2024"
            '%Y-%m-%d',     # "2024-02-29"
            '%d/%m/%Y',     # "29/02/2024"
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        self.logger.warning(f"Could not parse date: {date_str}")
        return None
        
    def _clean_description(self, desc: str) -> str:
        """Clean transaction description."""
        if pd.isna(desc):
            return ''
            
        # Remove extra whitespace and clean up
        desc = str(desc).strip()
        desc = re.sub(r'\s+', ' ', desc)  # Replace multiple spaces with single space
        
        return desc
        
    def _clean_amount(self, amount: str) -> str:
        """Clean monetary amount."""
        if pd.isna(amount) or str(amount).strip() == '':
            return ''
            
        # Remove commas and clean
        amount = str(amount).replace(',', '').strip()
        
        # Validate it's a number
        try:
            float(amount)
            return amount
        except ValueError:
            return ''
            
    def _map_transfer_account(self, description: str) -> str:
        """Map transaction description to appropriate transfer account."""
        if pd.isna(description):
            return ''
            
        desc_upper = str(description).upper()
        
        # Interest transactions
        if 'INTEREST WITHHELD' in desc_upper:
            return 'Expenses:Banking Costs:Interest'
        elif 'INTEREST PAY SYS-GEN' in desc_upper:
            return 'Income:Interest Income'
        
        # All other transactions left blank for manual coding
        return ''
        
    def _is_new_format(self, columns) -> bool:
        """Detect if this is the new CSV format (2025-03 onwards)."""
        new_format_indicators = ['Book date', 'Credit/debit indicator', 'Account number(BBAN)']
        column_str = ' '.join(str(col) for col in columns)
        
        # Check if we have key indicators of the new format
        matches = sum(1 for indicator in new_format_indicators if indicator in column_str)
        return matches >= 2  # Need at least 2 indicators
        
    def _process_new_format(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Process the new CSV format (2025-03 onwards)."""
        try:
            # Required columns for new format
            required_columns = ['Book date', 'Description', 'Amount', 'Credit/debit indicator']
            
            # Check if all required columns exist
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                self.logger.error(f"Missing required columns in new format: {missing_cols}")
                return None
                
            # Filter valid transactions
            df_filtered = df[df['Book date'].notna() & df['Description'].notna()].copy()
            
            if df_filtered.empty:
                return None
                
            # Convert to standardized format
            output_data = []
            
            for _, row in df_filtered.iterrows():
                # Clean and parse date
                date_str = self._clean_date_new_format(row['Book date'])
                if not date_str:
                    continue
                    
                # Parse amount and debit/credit indicator
                amount = self._clean_amount(row['Amount'])
                indicator = str(row['Credit/debit indicator']).strip().lower()
                
                # Skip if no valid amount
                if not amount:
                    continue
                
                # Determine debit/credit based on indicator
                debit = amount if indicator == 'debit' else ''
                credit = amount if indicator == 'credit' else ''
                
                output_data.append({
                    'Date': date_str,
                    'Description': self._clean_description(row['Description']),
                    'Debit': debit,
                    'Credit': credit
                })
                
            return pd.DataFrame(output_data)
            
        except Exception as e:
            self.logger.error(f"Error processing new format: {e}")
            return None
            
    def _process_legacy_format(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Process the legacy CSV format (pre-2025-03)."""
        # Map columns to expected names
        column_mapping = self._map_columns(df.columns)
        if not column_mapping:
            self.logger.error("Could not map required columns")
            return None
            
        # Filter to only keep transactions (stop at end markers)
        df = self._filter_transactions(df)
        
        # Extract required columns
        required_cols = ['Posting Date', 'Description', 'Debit Amount', 'Credit Amount']
        mapped_data = {}
        
        for req_col in required_cols:
            if req_col in column_mapping:
                mapped_data[req_col] = df[column_mapping[req_col]]
            else:
                self.logger.error(f"Required column '{req_col}' not found")
                return None
                
        # Create output DataFrame
        output_df = pd.DataFrame(mapped_data)
        
        # Return raw data for processing by _clean_data method
        return output_df
        
    def _clean_date_new_format(self, date_str: str) -> Optional[str]:
        """Clean and convert date string from new format to YYYY-MM-DD format."""
        if pd.isna(date_str):
            return None
            
        date_str = str(date_str).strip()
        
        # New format supports multiple date styles
        formats = [
            '%d-%m-%Y',     # "30-06-2025" (new DD-MM-YYYY format)
            '%b %d, %Y',    # "Mar 31, 2025" (original new format)
            '%B %d, %Y',    # "March 31, 2025"  
            '%m/%d/%Y',     # "03/31/2025"
            '%Y-%m-%d',     # "2025-03-31"
        ]
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
                
        self.logger.warning(f"Could not parse date from new format: {date_str}")
        return None