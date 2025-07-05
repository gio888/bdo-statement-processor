# BDO Statement Processor - Monthly Workflow

**Simple step-by-step guide for monthly BDO statement processing**

## Overview

The monthly workflow automatically processes new BDO statement files and creates a single combined output file ready for import into your accounting software.

## Prerequisites

1. **Python Environment**: Virtual environment with required packages installed
2. **BDO Files**: Downloaded CSV files from BDO online banking
3. **File Location**: All BDO CSV files in the designated Google Drive folder

## Monthly Processing Steps

### Step 1: Download BDO Statements

1. Log into BDO online banking
2. Download CSV statements for both accounts:
   - Checking account (007318007064)
   - Savings account (007310159087)
3. Save files to: `/Users/gio/Library/CloudStorage/GoogleDrive-gbacareza@gmail.com/My Drive/Money/BDO`
4. Ensure files follow naming pattern: `My_Transactions BDO [Checking|Savings] [account_number] YYYY-MM-DD.csv`

### Step 2: Run Monthly Processing

1. Open Terminal
2. Navigate to project directory:
   ```bash
   cd /Users/gio/Code/bdo-statement-processor
   ```
3. Activate virtual environment:
   ```bash
   source venv/bin/activate
   ```
4. Run monthly processing:
   ```bash
   python main.py --monthly
   ```

### Step 3: Confirm Processing

The script will:
1. **Detect new files** that haven't been processed yet
2. **Ask for confirmation**: "Processing files for [Month Year], correct? (Y/n)"
3. **Show processing status** for each file
4. **Create combined output file**: `for_import_My_Transactions BDO YYYY-MM-DD.csv`

### Step 4: Review Output

The generated file contains:
- **Date**: Original M/D/YYYY format (e.g., 2/29/2024)
- **Description**: Clean transaction descriptions
- **Debit**: Amount leaving account (blank if none)
- **Credit**: Amount entering account (blank if none)
- **Account**: BDO account category (auto-mapped)
- **Transfer Account**: Empty (for manual categorization)

### Step 5: Import to Accounting Software

1. Locate the output file: `for_import_My_Transactions BDO YYYY-MM-DD.csv`
2. Import into your accounting software
3. Manually categorize the Transfer Account column as needed

## What the Script Does Automatically

✅ **Detects new files** - Only processes files that haven't been processed before  
✅ **Combines accounts** - Merges checking and savings transactions into one file  
✅ **Sorts chronologically** - Orders all transactions by date  
✅ **Preserves date format** - Keeps M/D/YYYY format for compatibility  
✅ **Maps accounts** - Automatically categorizes BDO account types  
✅ **Handles missing files** - Continues processing if one account is missing  

## Expected Output Format

```csv
Date,Description,Debit,Credit,Account,Transfer Account
2/29/2024,INTEREST PAY SYS-GEN,,2.33,Assets:Current Assets:Banks Local:BDO Current,
2/29/2024,INTEREST PAY SYS-GEN,,2.76,Assets:Current Assets:Banks Local:BDO Savings,
```

## Troubleshooting

### ❌ "No new files found to process"
**Cause**: All files have already been processed  
**Solution**: Check if you've downloaded the latest statements from BDO

### ❌ "Missing [account] account data for [Month]"
**Cause**: Only one account's CSV file was found  
**Solution**: Download the missing account's statement, or continue with partial data

### ❌ "Invalid date format in filename"
**Cause**: BDO file doesn't match expected naming pattern  
**Solution**: Rename file to: `My_Transactions BDO [Checking|Savings] [account] YYYY-MM-DD.csv`

### ❌ "Could not parse date"
**Cause**: Date in filename is not in YYYY-MM-DD format  
**Solution**: Check and correct the date in the filename

## File Organization

```
BDO Folder/
├── My_Transactions BDO Checking 007318007064 2024-03-31.csv (original)
├── My_Transactions BDO Savings 007310159087 2024-03-31.csv (original)
└── for_import_My_Transactions BDO 2024-03-31.csv (output)
```

## Success Indicators

✅ **Files processed**: Shows number of files successfully processed  
✅ **Transactions processed**: Shows total number of transactions  
✅ **Output file created**: Confirms the combined file was generated  
✅ **No errors**: Processing completed without failures  

## Common Workflow

**Monthly routine** (5 minutes):
1. Download BDO statements → Save to Google Drive folder
2. Run: `python main.py --monthly` → Confirm month
3. Import generated file → Into accounting software
4. Done! ✅

## Support

For technical issues:
- Check logs in `logs/bdo_processor.log`
- Run with debug mode: `python main.py --monthly --log-level DEBUG`
- Ensure file naming follows the expected pattern

---
*This workflow processes your BDO statements safely and efficiently each month.*