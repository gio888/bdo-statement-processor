"""File management utilities for BDO Statement Processor."""

import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

import config


class FileManager:
    """Handles file discovery, validation, and backup operations."""
    
    def __init__(self, input_dir: str = None):
        """Initialize FileManager with input directory."""
        self.input_dir = Path(input_dir or config.DEFAULT_INPUT_DIR)
        self.logger = logging.getLogger(__name__)
        
    def discover_files(self, from_date: datetime = None) -> List[Tuple[Path, dict]]:
        """
        Discover BDO CSV files matching the expected pattern.
        
        Args:
            from_date: Minimum date to process files from
            
        Returns:
            List of tuples containing (file_path, metadata_dict)
        """
        if not self.input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")
            
        from_date = from_date or config.MIN_PROCESS_DATE
        pattern = re.compile(config.FILE_PATTERN)
        files = []
        
        for file_path in self.input_dir.glob("*.csv"):
            try:
                metadata = self._extract_metadata(file_path, pattern)
                if metadata and metadata['date'] >= from_date:
                    files.append((file_path, metadata))
                    self.logger.info(f"Found eligible file: {file_path.name}")
                else:
                    self.logger.debug(f"Skipping file (date filter): {file_path.name}")
            except Exception as e:
                self.logger.warning(f"Error processing file {file_path.name}: {e}")
                
        # Sort by date for consistent processing order
        files.sort(key=lambda x: x[1]['date'])
        self.logger.info(f"Discovered {len(files)} eligible files")
        return files
        
    def _extract_metadata(self, file_path: Path, pattern: re.Pattern) -> Optional[dict]:
        """Extract metadata from filename using regex pattern."""
        match = pattern.search(file_path.name)
        if not match:
            return None
            
        account_type, account_number, date_str = match.groups()
        
        try:
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            self.logger.warning(f"Invalid date format in filename: {date_str}")
            return None
            
        return {
            'account_type': account_type,
            'account_number': account_number,
            'date': file_date,
            'date_str': date_str
        }
        
    def create_backup(self, file_path: Path) -> Optional[Path]:
        """
        Create a timestamped backup of an existing file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file, or None if no backup needed
        """
        if not file_path.exists():
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}{config.BACKUP_SUFFIX}_{timestamp}{file_path.suffix}"
        backup_path = file_path.parent / backup_name
        
        try:
            # Create backup by copying
            import shutil
            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path.name}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path.name}: {e}")
            return None
            
    def generate_output_path(self, input_path: Path, metadata: dict) -> Path:
        """
        Generate the output file path based on input file and metadata.
        
        Args:
            input_path: Original input file path
            metadata: File metadata dictionary
            
        Returns:
            Path for the output file
        """
        original_name = input_path.name
        output_name = f"{config.OUTPUT_PREFIX}{original_name}"
        return input_path.parent / output_name
        
    def validate_directory(self, directory: Path) -> bool:
        """
        Validate that a directory exists and is accessible.
        
        Args:
            directory: Directory path to validate
            
        Returns:
            True if directory is valid and accessible
        """
        if not directory.exists():
            self.logger.error(f"Directory does not exist: {directory}")
            return False
            
        if not directory.is_dir():
            self.logger.error(f"Path is not a directory: {directory}")
            return False
            
        if not os.access(directory, os.R_OK):
            self.logger.error(f"Directory is not readable: {directory}")
            return False
            
        return True
        
    def get_file_stats(self, files: List[Tuple[Path, dict]]) -> dict:
        """
        Generate statistics about discovered files.
        
        Args:
            files: List of (file_path, metadata) tuples
            
        Returns:
            Dictionary with file statistics
        """
        if not files:
            return {"total": 0, "by_account": {}, "date_range": None}
            
        stats = {
            "total": len(files),
            "by_account": {},
            "date_range": {
                "earliest": min(f[1]['date'] for f in files),
                "latest": max(f[1]['date'] for f in files)
            }
        }
        
        for _, metadata in files:
            account_type = metadata['account_type']
            if account_type not in stats["by_account"]:
                stats["by_account"][account_type] = 0
            stats["by_account"][account_type] += 1
            
        return stats