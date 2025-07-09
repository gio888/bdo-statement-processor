# BDO Statement Processor v2.0

A robust Python application to process BDO bank statement CSV files, extract transaction data, and prepare them for import into accounting software. Automatically handles multiple BDO CSV formats and combines checking/savings transactions into unified monthly reports.

## Quick Start (Monthly Workflow)

```bash
# Setup (one-time)
cd /Users/gio/Code/bdo-statement-processor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Monthly processing (processes all unprocessed months automatically)
python main.py --monthly
```

📖 **[See MONTHLY_WORKFLOW.md for detailed instructions](MONTHLY_WORKFLOW.md)**

## ✨ Version 2.0 Features

### 🚀 New in v2.0
- **Combined Monthly Output**: Single output file per month combining both checking and savings transactions
- **Dual CSV Format Support**: Automatically handles both legacy (pre-2025-03) and new BDO CSV formats
- **Smart Month Detection**: Automatically detects and processes all unprocessed months chronologically
- **Enhanced Transfer Account Mapping**: Automatically maps interest transactions to appropriate accounts
- **Intelligent Processing**: Only processes actual input files, ignores previously processed outputs

### 📊 Core Features
- **Automated File Discovery**: Scans for BDO CSV files matching the expected naming pattern
- **Smart CSV Parsing**: Dynamically detects header rows and handles various CSV formats
- **Date Format Support**: Handles multiple date formats (`Mar 31, 2025`, `30-06-2025`, etc.)
- **Account Mapping**: Automatically maps account types to accounting software categories
- **Comprehensive Logging**: Detailed logging with configurable levels
- **Dry Run Mode**: Preview what would be processed without making changes
- **Error Handling**: Graceful error handling with detailed reporting

## Installation

1. Navigate to project directory:
   ```bash
   cd /Users/gio/Code/bdo-statement-processor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Recommended: Monthly Workflow

Process all unprocessed months automatically:
```bash
python main.py --monthly
```

**What it does:**
- Detects all months with unprocessed files
- Processes them chronologically 
- Combines checking + savings into single monthly files
- Shows clear progress and summary

### Legacy: Individual File Processing

```bash
# Process all eligible files
python main.py

# Process specific files
python main.py --files "file1.csv" "file2.csv"

# Process files from specific date
python main.py --from-date "2024-03-01"

# Dry run to preview
python main.py --dry-run

# Debug mode
python main.py --log-level DEBUG
```

## File Requirements

### Input Files

BDO CSV files with this naming pattern:
```
My_Transactions BDO [Checking|Savings] [account_number] YYYY-MM-DD.csv
```

**Examples:**
- `My_Transactions BDO Checking xxxx 2025-06-30.csv`
- `My_Transactions BDO Savings xxxx 2025-06-30.csv`

### Supported CSV Formats

The system automatically detects and processes:

1. **Legacy Format** (pre-2025-03):
   - Date: `Feb 29, 2024`
   - Columns: `Posting Date`, `Debit Amount`, `Credit Amount`

2. **New Format v1** (2025-03):
   - Date: `Mar 31, 2025`  
   - Columns: `Book date`, `Amount`, `Credit/debit indicator`

3. **New Format v2** (2025-04+):
   - Date: `30-06-2025`
   - Columns: `Book date`, `Amount`, `Credit/debit indicator`

## Output

### Monthly Combined Files

**New v2.0 Format:**
```
for_import_My_Transactions BDO YYYY-MM.csv
```

**Examples:**
- `for_import_My_Transactions BDO 2025-06.csv` (June 2025 - all accounts combined)
- `for_import_My_Transactions BDO 2025-05.csv` (May 2025 - all accounts combined)

### Output Structure

Each monthly file contains:
```csv
Date,Description,Debit,Credit,Account,Transfer Account
```

### Account Mappings

- **Checking** → `Assets:Current Assets:Banks Local:BDO Current`
- **Savings** → `Assets:Current Assets:Banks Local:BDO Savings`

### Transfer Account Auto-Mapping

- **Interest Withheld** → `Expenses:Banking Costs:Interest`
- **Interest Pay** → `Income:Interest Income`
- **Other transactions** → Empty (for manual coding)

## Workflow Example

### Typical Monthly Processing (July 6, 2025)

```bash
$ python main.py --monthly

📅 Found 3 unprocessed months:
   - 2025-04 (2 files: Checking + Savings)
   - 2025-05 (2 files: Checking + Savings)  
   - 2025-06 (2 files: Checking + Savings)

🔄 Processing 2025-04...
✅ Processed 2 transactions from My_Transactions BDO Checking xxxx 2025-04-30.csv
✅ Processed 2 transactions from My_Transactions BDO Savings xxxx 2025-04-30.csv
✅ Created: for_import_My_Transactions BDO 2025-04.csv

🔄 Processing 2025-05...
✅ Processed 3 transactions from My_Transactions BDO Checking xxxx 2025-05-31.csv
✅ Processed 2 transactions from My_Transactions BDO Savings xxxx 2025-05-31.csv
✅ Created: for_import_My_Transactions BDO 2025-05.csv

🔄 Processing 2025-06...
✅ Processed 3 transactions from My_Transactions BDO Checking xxxx 2025-06-30.csv
✅ Processed 5 transactions from My_Transactions BDO Savings xxxx 2025-06-30.csv
✅ Created: for_import_My_Transactions BDO 2025-06.csv

📊 SUMMARY: Processed 3 of 3 months
```

## Configuration

### Settings

Key configuration options in `config.py`:

- `DEFAULT_INPUT_DIR`: Default directory to scan for files
- `MIN_PROCESS_DATE`: Minimum date to process files from (2024-02-01)
- `ACCOUNT_MAPPINGS`: Account type to category mappings
- `FILE_PATTERN`: Regex pattern for matching input filenames (excludes processed files)

### Input Directory

Default location:
```
/Users/gio/Library/CloudStorage/GoogleDrive-gbacareza@gmail.com/My Drive/Money/BDO
```

Override with: `--input-dir "/path/to/bdo/files"`

## Project Structure

```
bdo-statement-processor/
├── src/
│   ├── __init__.py
│   ├── processor.py          # Individual file processing
│   ├── monthly_processor.py  # Monthly workflow orchestration
│   ├── parser.py            # Dual-format CSV parsing
│   ├── file_manager.py      # File operations and discovery
│   └── utils.py             # Utility functions
├── tests/
│   ├── __init__.py
│   ├── test_processor.py    # Unit tests
│   └── sample_data/         # Test data
├── logs/                    # Application logs
├── config.py               # Configuration settings
├── main.py                # CLI entry point
├── requirements.txt       # Dependencies
├── MONTHLY_WORKFLOW.md    # Detailed workflow guide
└── README.md             # This file
```

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

## Troubleshooting

### Common Issues

1. **No files found**: Check input directory path and file naming pattern
2. **Date parsing errors**: System now handles multiple formats automatically
3. **Missing months**: System shows which months are unprocessed
4. **Empty transactions**: Normal for months with no banking activity

### Debug Mode

```bash
python main.py --monthly --log-level DEBUG
```

### Monthly Processing Issues

If monthly processing fails:
1. Check that input files follow naming convention
2. Verify files aren't corrupted
3. Run with `--dry-run` to preview
4. Check logs in `logs/bdo_processor.log`

## Dependencies

- **pandas**: CSV parsing and data manipulation
- **python-dateutil**: Flexible date parsing

## Changelog

### v2.0.0 (July 2025)
- **BREAKING**: Combined monthly output format
- **NEW**: Dual CSV format support (legacy + new BDO formats)
- **NEW**: Smart unprocessed month detection
- **NEW**: Automatic transfer account mapping for interest transactions
- **NEW**: Enhanced date format support (`DD-MM-YYYY`, `Mar 31, 2025`)
- **IMPROVED**: File discovery excludes processed files
- **IMPROVED**: Monthly workflow with progress tracking

### v1.0.0 (Initial Release)
- Basic CSV processing
- Individual file output
- Legacy format support

## License

This project is for personal use in processing BDO bank statements.
