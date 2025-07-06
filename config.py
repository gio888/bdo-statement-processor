"""Configuration settings for BDO Statement Processor."""

import os
from datetime import datetime

# File processing settings
DEFAULT_INPUT_DIR = "/Users/gio/Library/CloudStorage/GoogleDrive-gbacareza@gmail.com/My Drive/Money/BDO"
FILE_PATTERN = r"^My_Transactions BDO (Checking|Savings) (\d+) (\d{4}-\d{2}-\d{2})\.csv$"
MIN_PROCESS_DATE = datetime(2024, 2, 1)

# Account mappings
ACCOUNT_MAPPINGS = {
    "Checking": "Assets:Current Assets:Banks Local:BDO Current",
    "Savings": "Assets:Current Assets:Banks Local:BDO Savings"
}

# Output settings
OUTPUT_PREFIX = "for_import_"
BACKUP_SUFFIX = "_backup"

# CSV parsing settings
EXPECTED_COLUMNS = [
    "Posting Date",
    "Description", 
    "Branch",
    "Debit Amount",
    "Credit Amount",
    "Running Balance",
    "Currency",
    "Check Number"
]

# Alternative column names for fuzzy matching
COLUMN_ALTERNATIVES = {
    "Posting Date": ["Date", "Transaction Date", "Post Date", "Book date"],
    "Description": ["Transaction Description", "Details", "Particulars"],
    "Debit Amount": ["Debit", "Debit Amt", "Withdrawal"],
    "Credit Amount": ["Credit", "Credit Amt", "Deposit"],
    "Running Balance": ["Balance", "Account Balance", "Current Balance"]
}

# New CSV format (2025-03 onwards) column mappings
NEW_FORMAT_COLUMNS = {
    "Book date": "Posting Date",
    "Description": "Description", 
    "Amount": "Amount",
    "Credit/debit indicator": "Credit/debit indicator"
}

# Data validation settings
END_OF_REPORT_MARKERS = [
    "** End of Report **",
    "End of Report",
    "*** End of Report ***",
    "Page",
    "Generated on"
]

# Logging configuration
LOG_DIR = "logs"
LOG_FILE = "bdo_processor.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Default CLI settings
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_DRY_RUN = False

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)