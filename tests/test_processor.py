"""Tests for BDO Statement Processor."""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pandas as pd
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.file_manager import FileManager
from src.parser import BDOParser
from src.processor import BDOProcessor
from src.utils import extract_account_info, validate_date_string, clean_filename


class TestFileManager(unittest.TestCase):
    """Test cases for FileManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManager(self.temp_dir)
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        
    def test_extract_metadata(self):
        """Test metadata extraction from filename."""
        import re
        import config
        
        pattern = re.compile(config.FILE_PATTERN)
        
        # Test valid filename
        filename = "My_Transactions BDO Checking 007310159087 2024-02-29.csv"
        result = self.file_manager._extract_metadata(Path(filename), pattern)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['account_type'], 'Checking')
        self.assertEqual(result['account_number'], '007310159087')
        self.assertEqual(result['date_str'], '2024-02-29')
        self.assertEqual(result['date'], datetime(2024, 2, 29))
        
    def test_extract_metadata_invalid(self):
        """Test metadata extraction with invalid filename."""
        import re
        import config
        
        pattern = re.compile(config.FILE_PATTERN)
        
        # Test invalid filename
        filename = "invalid_file.csv"
        result = self.file_manager._extract_metadata(Path(filename), pattern)
        
        self.assertIsNone(result)
        
    def test_generate_output_path(self):
        """Test output path generation."""
        input_path = Path(self.temp_dir) / "My_Transactions BDO Checking 007310159087 2024-02-29.csv"
        metadata = {'account_type': 'Checking'}
        
        output_path = self.file_manager.generate_output_path(input_path, metadata)
        
        self.assertTrue(output_path.name.startswith('for_import_'))
        self.assertTrue(output_path.name.endswith('.csv'))


class TestBDOParser(unittest.TestCase):
    """Test cases for BDOParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = BDOParser()
        
    def test_looks_like_date(self):
        """Test date pattern recognition."""
        # Valid date patterns
        self.assertTrue(self.parser._looks_like_date("Feb 29, 2024"))
        self.assertTrue(self.parser._looks_like_date("02/29/2024"))
        self.assertTrue(self.parser._looks_like_date("2024-02-29"))
        
        # Invalid patterns
        self.assertFalse(self.parser._looks_like_date("Not a date"))
        self.assertFalse(self.parser._looks_like_date("123456"))
        self.assertFalse(self.parser._looks_like_date(""))
        
    def test_clean_date(self):
        """Test date cleaning and conversion."""
        # Test valid dates
        self.assertEqual(self.parser._clean_date("Feb 29, 2024"), "2024-02-29")
        self.assertEqual(self.parser._clean_date("02/29/2024"), "2024-02-29")
        self.assertEqual(self.parser._clean_date("2024-02-29"), "2024-02-29")
        
        # Test invalid dates
        self.assertIsNone(self.parser._clean_date("Invalid date"))
        self.assertIsNone(self.parser._clean_date(""))
        self.assertIsNone(self.parser._clean_date(None))
        
    def test_clean_amount(self):
        """Test amount cleaning."""
        # Test valid amounts
        self.assertEqual(self.parser._clean_amount("1,234.56"), "1234.56")
        self.assertEqual(self.parser._clean_amount("123.45"), "123.45")
        self.assertEqual(self.parser._clean_amount("0.00"), "0.00")
        
        # Test invalid amounts
        self.assertEqual(self.parser._clean_amount(""), "")
        self.assertEqual(self.parser._clean_amount("Not a number"), "")
        self.assertEqual(self.parser._clean_amount(None), "")
        
    def test_clean_description(self):
        """Test description cleaning."""
        # Test normal description
        self.assertEqual(self.parser._clean_description("INTEREST PAY SYS-GEN"), "INTEREST PAY SYS-GEN")
        
        # Test description with extra spaces
        self.assertEqual(self.parser._clean_description("  MULTIPLE   SPACES  "), "MULTIPLE SPACES")
        
        # Test empty description
        self.assertEqual(self.parser._clean_description(""), "")
        self.assertEqual(self.parser._clean_description(None), "")


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""
    
    def test_extract_account_info(self):
        """Test account information extraction."""
        filename = "My_Transactions BDO Savings 007310159087 2024-02-29.csv"
        result = extract_account_info(filename)
        
        self.assertEqual(result['account_type'], 'Savings')
        self.assertEqual(result['account_number'], '007310159087')
        self.assertEqual(result['date_str'], '2024-02-29')
        self.assertIn('account_name', result)
        
    def test_validate_date_string(self):
        """Test date string validation."""
        # Test valid dates
        result = validate_date_string("2024-02-29")
        self.assertEqual(result, datetime(2024, 2, 29))
        
        result = validate_date_string("02/29/2024")
        self.assertEqual(result, datetime(2024, 2, 29))
        
        # Test invalid dates
        with self.assertRaises(ValueError):
            validate_date_string("Invalid date")
            
        with self.assertRaises(ValueError):
            validate_date_string("")
            
    def test_clean_filename(self):
        """Test filename cleaning."""
        # Test filename with invalid characters
        result = clean_filename("file<>name:|?.csv")
        self.assertEqual(result, "file_name_.csv")
        
        # Test filename with multiple underscores
        result = clean_filename("file___name.csv")
        self.assertEqual(result, "file_name.csv")
        
        # Test normal filename
        result = clean_filename("normal_file.csv")
        self.assertEqual(result, "normal_file.csv")


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.create_sample_csv()
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
        
    def create_sample_csv(self):
        """Create a sample BDO CSV file for testing."""
        sample_content = """,,,,,,,My Transactions,,,,
Account No:,,007310159087,,,,Generated By:,,,GIO8888,,
Account Name:,,VALUED CLIENT,,,,Tran Type:,,,All,,
Account Type:,,SA,,,,Amount Range:,,,,,
Account Currency:,,PHP,,,,Period Covered:,,,From 02/01/2024 To 02/29/2024,,
Posting Date,Description,,Branch,Debit Amount,,Credit Amount,,Running Balance,,Currency,Check Number
"Feb 29, 2024",INTEREST WITHHELD,, ,0.55,,,,"55,677.05",,PHP,
"Feb 29, 2024",INTEREST PAY SYS-GEN,, ,,,2.76,,"55,677.60",,PHP,
"Feb 28, 2024",ONLINE TRANSFER,, ,500.00,,,,"55,674.84",,PHP,
"Feb 27, 2024",ATM WITHDRAWAL,, ,1000.00,,,,"56,174.84",,PHP,
,,,,,,,,,,Page 1 of 1,
,,,,,** End of Report **,,,,,,
"""
        
        sample_file = Path(self.temp_dir) / "My_Transactions BDO Savings 007310159087 2024-02-29.csv"
        with open(sample_file, 'w') as f:
            f.write(sample_content)
            
    def test_complete_processing(self):
        """Test complete processing workflow."""
        # Process the sample file
        processor = BDOProcessor(input_dir=self.temp_dir, dry_run=True)
        stats = processor.process_all()
        
        # Verify statistics
        self.assertEqual(stats['files_discovered'], 1)
        self.assertEqual(stats['files_processed'], 1)
        self.assertEqual(stats['files_failed'], 0)
        self.assertTrue(stats['transactions_processed'] > 0)


if __name__ == '__main__':
    unittest.main()