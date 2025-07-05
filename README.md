# BDO Statement Processor

A robust Python application to process BDO bank statement CSV files, extract transaction data, and prepare them for import into accounting software.

## Quick Start (Monthly Workflow)

```bash
# Setup (one-time)
git clone https://github.com/gio888/bdo-statement-processor
cd bdo-statement-processor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Monthly processing
python main.py --monthly
```

📖 **[See MONTHLY_WORKFLOW.md for detailed instructions](MONTHLY_WORKFLOW.md)**

## Features

- **Automated File Discovery**: Scans for BDO CSV files matching the expected naming pattern
- **Smart CSV Parsing**: Dynamically detects header rows and handles various CSV formats
- **Date Filtering**: Processes files from February 2024 onwards by default
- **Account Mapping**: Automatically maps account types to accounting software categories
- **Backup Management**: Creates timestamped backups of existing processed files
- **Comprehensive Logging**: Detailed logging with configurable levels
- **Dry Run Mode**: Preview what would be processed without making changes
- **Error Handling**: Graceful error handling with detailed reporting

## Installation

1. Clone or download the project:
   ```bash
   cd /Users/gio/Code/bdo-statement-processor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Make the main script executable:
   ```bash
   chmod +x main.py
   ```

## Usage

### Basic Usage

Process all eligible BDO CSV files with default settings:
```bash
python main.py
```

### Command Line Options

```bash
# Use custom input directory
python main.py --input-dir "/path/to/bdo/files"

# Process files from specific date
python main.py --from-date "2024-03-01"

# Dry run to see what would be processed
python main.py --dry-run

# Enable debug logging
python main.py --log-level DEBUG

# Process specific files
python main.py --files "file1.csv" "file2.csv"

# Use custom log file
python main.py --log-file "/path/to/custom.log"
```

### Help

```bash
python main.py --help
```

## File Requirements

### Input Files

The application expects BDO CSV files with this naming pattern:
```
My_Transactions BDO [Checking|Savings] [account_number] YYYY-MM-DD.csv
```

Examples:
- `My_Transactions BDO Checking 007310159087 2024-02-29.csv`
- `My_Transactions BDO Savings 007310159087 2024-03-15.csv`

### Input Directory

By default, the application looks for files in:
```
/Users/gio/Library/CloudStorage/GoogleDrive-gbacareza@gmail.com/My Drive/Money/BDO
```

You can specify a different directory using the `--input-dir` option.

## Output

### Processed Files

The application generates CSV files with this naming pattern:
```
for_import_My_Transactions BDO [Checking|Savings] [account_number] YYYY-MM-DD.csv
```

### Output Format

The processed CSV files contain these columns:
- **Date**: Transaction date in YYYY-MM-DD format
- **Description**: Cleaned transaction description
- **Debit**: Debit amount (empty string if none)
- **Credit**: Credit amount (empty string if none)
- **Account**: Mapped account category
- **Transfer Account**: Empty (to be filled manually)

### Account Mappings

- **Checking** → `Assets:Current Assets:Banks Local:BDO Current`
- **Savings** → `Assets:Current Assets:Banks Local:BDO Savings`

## Configuration

### Settings

Key configuration options are in `config.py`:

- `DEFAULT_INPUT_DIR`: Default directory to scan for files
- `MIN_PROCESS_DATE`: Minimum date to process files from (2024-02-01)
- `ACCOUNT_MAPPINGS`: Account type to category mappings
- `FILE_PATTERN`: Regular expression for matching filenames

### Logging

Logs are written to `logs/bdo_processor.log` by default. The log level can be adjusted using the `--log-level` option.

## Project Structure

```
bdo-statement-processor/
├── src/
│   ├── __init__.py
│   ├── processor.py          # Main processing orchestration
│   ├── parser.py            # CSV parsing with dynamic header detection
│   ├── file_manager.py      # File operations and backup handling
│   └── utils.py             # Utility functions and validation
├── tests/
│   ├── __init__.py
│   ├── test_processor.py    # Unit tests
│   └── sample_data/         # Sample CSV files for testing
├── logs/                    # Log files directory
├── config.py               # Configuration settings
├── main.py                # Entry point
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Or run specific tests:
```bash
python -m unittest tests.test_processor
```

## Error Handling

The application handles various error conditions gracefully:

- **Missing Files**: Skips files that don't exist or are inaccessible
- **Invalid CSV Format**: Logs warnings and continues with other files
- **Date Parsing Errors**: Attempts multiple date formats before giving up
- **Empty Files**: Detects and skips files with no transaction data
- **Encoding Issues**: Tries multiple encodings to read CSV files

## Backup Strategy

When processing files, the application:

1. Checks if an output file already exists
2. Creates a timestamped backup with the format: `original_filename_backup_YYYYMMDD_HHMMSS.csv`
3. Writes the new processed file

This ensures no data is lost during reprocessing.

## Monthly Processing Workflow

For regular monthly processing:

1. Download new BDO CSV files to the input directory
2. Run the processor: `python main.py`
3. Review the processing report for any issues
4. Import the generated `for_import_*.csv` files into your accounting software

## Troubleshooting

### Common Issues

1. **No files found**: Check the input directory path and file naming pattern
2. **Permission errors**: Ensure the application has read/write access to the directories
3. **Date parsing errors**: Verify the date format in the CSV files matches expected patterns
4. **Empty output**: Check that the CSV files contain transaction data in the expected format

### Debug Mode

For detailed troubleshooting, run with debug logging:
```bash
python main.py --log-level DEBUG
```

This will provide verbose output about file processing steps.

## Dependencies

- **pandas**: For CSV parsing and data manipulation
- **python-dateutil**: For flexible date parsing

## Version

BDO Statement Processor 1.0.0

## License

This project is for personal use in processing BDO bank statements.