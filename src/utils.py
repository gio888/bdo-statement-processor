"""Utility functions and validation helpers for BDO Statement Processor."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Union
import pandas as pd

import config


def setup_logging(log_level: str = None, log_file: str = None) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    log_level = log_level or config.DEFAULT_LOG_LEVEL
    log_file = log_file or Path(config.LOG_DIR) / config.LOG_FILE
    
    # Create log directory if it doesn't exist
    Path(log_file).parent.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=config.LOG_FORMAT,
        datefmt=config.LOG_DATE_FORMAT,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    
    return logger


def validate_file_path(file_path: Union[str, Path]) -> Path:
    """
    Validate and convert file path to Path object.
    
    Args:
        file_path: File path as string or Path object
        
    Returns:
        Validated Path object
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If path is invalid
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
        
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
        
    return path


def validate_directory_path(dir_path: Union[str, Path]) -> Path:
    """
    Validate and convert directory path to Path object.
    
    Args:
        dir_path: Directory path as string or Path object
        
    Returns:
        Validated Path object
        
    Raises:
        FileNotFoundError: If directory doesn't exist
        ValueError: If path is invalid
    """
    path = Path(dir_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
        
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
        
    return path


def validate_date_string(date_str: str) -> datetime:
    """
    Validate and parse date string.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Parsed datetime object
        
    Raises:
        ValueError: If date string is invalid
    """
    if not date_str:
        raise ValueError("Date string cannot be empty")
        
    # Try common date formats
    formats = [
        '%Y-%m-%d',         # "2024-02-01"
        '%m/%d/%Y',         # "02/01/2024"
        '%d/%m/%Y',         # "01/02/2024"
        '%Y-%m-%d %H:%M:%S', # "2024-02-01 00:00:00"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
            
    raise ValueError(f"Invalid date format: {date_str}")


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    # Remove invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    
    return cleaned


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
        
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
        
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_csv_structure(df: pd.DataFrame, required_columns: List[str] = None) -> List[str]:
    """
    Validate CSV DataFrame structure.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Returns:
        List of validation errors
    """
    errors = []
    
    if df.empty:
        errors.append("DataFrame is empty")
        return errors
        
    # Check required columns
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
            
    # Check for completely empty columns
    empty_columns = [col for col in df.columns if df[col].isna().all()]
    if empty_columns:
        errors.append(f"Completely empty columns: {empty_columns}")
        
    # Check row count
    if len(df) == 0:
        errors.append("No data rows found")
        
    return errors


def extract_account_info(filename: str) -> Dict[str, str]:
    """
    Extract account information from filename.
    
    Args:
        filename: BDO statement filename
        
    Returns:
        Dictionary with account information
    """
    pattern = re.compile(config.FILE_PATTERN)
    match = pattern.search(filename)
    
    if not match:
        return {}
        
    account_type, account_number, date_str = match.groups()
    
    return {
        'account_type': account_type,
        'account_number': account_number,
        'date_str': date_str,
        'account_name': config.ACCOUNT_MAPPINGS.get(account_type, f"Unknown:{account_type}")
    }


def format_amount(amount: Union[str, float, int]) -> str:
    """
    Format monetary amount for display.
    
    Args:
        amount: Amount to format
        
    Returns:
        Formatted amount string
    """
    if pd.isna(amount) or amount == '' or amount is None:
        return '0.00'
        
    try:
        # Convert to float
        amount_float = float(str(amount).replace(',', ''))
        return f"{amount_float:.2f}"
    except (ValueError, TypeError):
        return '0.00'


def is_valid_transaction_row(row: pd.Series) -> bool:
    """
    Check if a row represents a valid transaction.
    
    Args:
        row: DataFrame row
        
    Returns:
        True if row appears to be a valid transaction
    """
    # Check if first column (date) is not empty
    if pd.isna(row.iloc[0]) or str(row.iloc[0]).strip() == '':
        return False
        
    # Check if it looks like a date
    date_str = str(row.iloc[0]).strip()
    date_patterns = [
        r'\w{3}\s+\d{1,2},\s+\d{4}',  # "Feb 29, 2024"
        r'\d{1,2}/\d{1,2}/\d{4}',     # "02/29/2024"
        r'\d{4}-\d{2}-\d{2}',         # "2024-02-29"
    ]
    
    has_date_pattern = any(re.search(pattern, date_str) for pattern in date_patterns)
    if not has_date_pattern:
        return False
        
    # Check if row has enough columns
    if len(row) < 4:
        return False
        
    # Check if it's not an end marker
    row_str = ' '.join(str(cell) for cell in row if pd.notna(cell))
    if any(marker in row_str for marker in config.END_OF_REPORT_MARKERS):
        return False
        
    return True


def create_summary_report(stats: Dict) -> str:
    """
    Create a formatted summary report.
    
    Args:
        stats: Processing statistics dictionary
        
    Returns:
        Formatted report string
    """
    report_lines = [
        "BDO Statement Processing Summary",
        "=" * 50,
        f"Files discovered: {stats.get('files_discovered', 0)}",
        f"Files processed successfully: {stats.get('files_processed', 0)}",
        f"Files failed: {stats.get('files_failed', 0)}",
        f"Files skipped: {stats.get('files_skipped', 0)}",
        f"Total transactions processed: {stats.get('transactions_processed', 0)}",
        f"Backup files created: {stats.get('backups_created', 0)}",
        ""
    ]
    
    # Add error details if any
    errors = stats.get('errors', [])
    if errors:
        report_lines.extend([
            f"Errors encountered ({len(errors)}):",
            "-" * 30
        ])
        for error in errors:
            report_lines.append(f"  • {error}")
        report_lines.append("")
        
    # Add success rate
    total_files = stats.get('files_discovered', 0)
    successful_files = stats.get('files_processed', 0)
    if total_files > 0:
        success_rate = (successful_files / total_files) * 100
        report_lines.append(f"Success rate: {success_rate:.1f}%")
    
    return "\n".join(report_lines)


def get_file_info(file_path: Path) -> Dict[str, str]:
    """
    Get file information including size and modification time.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    try:
        stat = file_path.stat()
        return {
            'size': format_file_size(stat.st_size),
            'size_bytes': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'name': file_path.name,
            'path': str(file_path)
        }
    except Exception as e:
        return {
            'size': 'Unknown',
            'size_bytes': 0,
            'modified': 'Unknown',
            'name': file_path.name,
            'path': str(file_path),
            'error': str(e)
        }