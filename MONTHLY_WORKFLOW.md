# BDO Statement Processor v2.0 - Monthly Workflow

**Complete guide for automated monthly BDO statement processing**

## Overview

The v2.0 monthly workflow automatically detects and processes ALL unprocessed months, combining checking and savings transactions into unified monthly files ready for accounting software import.

## ✨ What's New in v2.0

- **🔄 Automatic Month Detection**: Finds all unprocessed months automatically
- **📁 Combined Output**: Single file per month (not per account)
- **🚀 Batch Processing**: Processes multiple months chronologically 
- **🧠 Smart Detection**: Only processes actual input files, ignores processed outputs
- **🎯 Zero Configuration**: No confirmations needed, fully automated

## Prerequisites

1. **Python Environment**: Virtual environment with required packages
2. **BDO Files**: Downloaded CSV files from BDO online banking
3. **File Location**: All BDO CSV files in Google Drive folder

## Monthly Processing Steps

### Step 1: Download BDO Statements

1. **Log into BDO online banking**
2. **Download CSV statements** for both accounts:
   - Checking account (007318007064)
   - Savings account (007310159087)
3. **Save to designated folder**:
   ```
   /Users/gio/Library/CloudStorage/GoogleDrive-gbacareza@gmail.com/My Drive/Money/BDO
   ```
4. **Verify naming pattern**:
   ```
   My_Transactions BDO Checking 007318007064 2025-06-30.csv
   My_Transactions BDO Savings 007310159087 2025-06-30.csv
   ```

### Step 2: Run Monthly Processing

1. **Open Terminal**
2. **Navigate to project**:
   ```bash
   cd /Users/gio/Code/bdo-statement-processor
   ```
3. **Activate environment**:
   ```bash
   source venv/bin/activate
   ```
4. **Run processing**:
   ```bash
   python main.py --monthly
   ```

### Step 3: Review Automatic Processing

The system will automatically:

```bash
📅 Found 3 unprocessed months:
   - 2025-04 (2 files: Checking + Savings)
   - 2025-05 (2 files: Checking + Savings)  
   - 2025-06 (2 files: Checking + Savings)

🔄 Processing 2025-04...
✅ Processed 2 transactions from My_Transactions BDO Checking 007318007064 2025-04-30.csv
✅ Processed 2 transactions from My_Transactions BDO Savings 007310159087 2025-04-30.csv
✅ Created: for_import_My_Transactions BDO 2025-04.csv

🔄 Processing 2025-05...
✅ Processed 3 transactions from My_Transactions BDO Checking 007318007064 2025-05-31.csv  
✅ Processed 2 transactions from My_Transactions BDO Savings 007310159087 2025-05-31.csv
✅ Created: for_import_My_Transactions BDO 2025-05.csv

🔄 Processing 2025-06...
✅ Processed 3 transactions from My_Transactions BDO Checking 007318007064 2025-06-30.csv
✅ Processed 5 transactions from My_Transactions BDO Savings 007310159087 2025-06-30.csv
✅ Created: for_import_My_Transactions BDO 2025-06.csv

📊 SUMMARY: Processed 3 of 3 months
```

### Step 4: Review Output Files

**New v2.0 Output Format:**
```
for_import_My_Transactions BDO 2025-06.csv
for_import_My_Transactions BDO 2025-05.csv  
for_import_My_Transactions BDO 2025-04.csv
```

**Each file contains:**
- **Combined transactions** from both checking and savings
- **Chronological order** by transaction date
- **M/D/YYYY date format** (e.g., 6/30/2025)
- **Auto-mapped transfer accounts** for interest transactions

### Step 5: Import to Accounting Software

1. **Locate output files** (one per month)
2. **Import each monthly file** into accounting software
3. **Verify auto-mapped transactions**:
   - Interest Withheld → `Expenses:Banking Costs:Interest` 
   - Interest Pay → `Income:Interest Income`
4. **Manually categorize** other transactions as needed

## What the System Does Automatically

### 🔍 Smart File Detection
- ✅ Scans all CSV files in directory
- ✅ Identifies unprocessed months
- ✅ Ignores already-processed files  
- ✅ Groups files by month automatically

### 🔄 Intelligent Processing  
- ✅ Processes months chronologically
- ✅ Combines checking + savings transactions
- ✅ Handles multiple BDO CSV formats
- ✅ Auto-maps interest transactions
- ✅ Preserves M/D/YYYY date format

### 🛡️ Error Handling
- ✅ Continues if one account missing
- ✅ Skips months with no transactions  
- ✅ Logs all processing details
- ✅ Shows clear progress and summary

## Expected Output Structure

```csv
Date,Description,Debit,Credit,Account,Transfer Account
6/30/2025,INTEREST WITHHELD,0.62,,Assets:Current Assets:Banks Local:BDO Current,Expenses:Banking Costs:Interest
6/30/2025,INTEREST PAY SYS-GEN,,3.10,Assets:Current Assets:Banks Local:BDO Current,Income:Interest Income
6/30/2025,FT-NDBWEB-20250601-46189953 DBFT,156079.25,,Assets:Current Assets:Banks Local:BDO Current,
6/30/2025,INTEREST WITHHELD,0.31,,Assets:Current Assets:Banks Local:BDO Savings,Expenses:Banking Costs:Interest
6/30/2025,INTEREST PAY SYS-GEN,,1.56,Assets:Current Assets:Banks Local:BDO Savings,Income:Interest Income
```

## Supported BDO CSV Formats

The system automatically detects and handles:

### Legacy Format (pre-2025-03)
```
Posting Date,Description,Branch,Debit Amount,Credit Amount,Running Balance
Feb 29, 2024,INTEREST PAY SYS-GEN,MAIN,0.00,2.33,15233.45
```

### New Format v1 (2025-03)  
```
Account number(BBAN),Description,Book date,Amount,Credit/debit indicator
007318007064,INTEREST PAY SYS-GEN,"Mar 31, 2025",2.44,Credit
```

### New Format v2 (2025-04+)
```
Account number(IBAN),Account number(BBAN),Description,Book date,Amount,Credit/debit indicator
,007318007064,INTEREST PAY SYS-GEN,30-06-2025,3.10,Credit
```

## Scenarios & Examples

### 📅 Normal Monthly Run (July 6, 2025)
**Situation**: Processing June 2025 statements  
**Command**: `python main.py --monthly`  
**Result**: Creates `for_import_My_Transactions BDO 2025-06.csv`

### 📅 Catching Up Multiple Months
**Situation**: Missed processing for 3 months  
**Command**: `python main.py --monthly`  
**Result**: Processes March, April, May automatically in order

### 📅 No New Files  
**Situation**: Already processed current month  
**Command**: `python main.py --monthly`  
**Result**: "✅ No unprocessed months found!"

### 📅 Missing Account Data
**Situation**: Only checking file available for a month  
**Result**: 
```
⚠️  WARNING: Missing Savings account data for June 2025
   Processing will continue with available data
✅ Created: for_import_My_Transactions BDO 2025-06.csv
```

## Troubleshooting

### ❌ "No unprocessed months found"
**Cause**: All available files have been processed  
**Solution**: Download new statements from BDO, or check if already up-to-date

### ❌ "Could not parse date from new format"  
**Cause**: BDO introduced new date format not yet supported  
**Solution**: Check logs and report new format for system update

### ❌ "No transactions found in file"
**Cause**: CSV file is empty or corrupted  
**Solution**: Re-download file from BDO, or normal for months with no activity

### ❌ "File not found" 
**Cause**: CSV file doesn't match expected naming pattern  
**Solution**: Rename to: `My_Transactions BDO [Checking|Savings] [account] YYYY-MM-DD.csv`

## File Organization After Processing

```
BDO Folder/
├── My_Transactions BDO Checking 007318007064 2025-06-30.csv (input)
├── My_Transactions BDO Savings 007310159087 2025-06-30.csv (input)
├── for_import_My_Transactions BDO 2025-06.csv (📁 COMBINED OUTPUT)
├── My_Transactions BDO Checking 007318007064 2025-05-31.csv (input)
├── My_Transactions BDO Savings 007310159087 2025-05-31.csv (input)
└── for_import_My_Transactions BDO 2025-05.csv (📁 COMBINED OUTPUT)
```

## Advanced Usage

### Preview Mode (Dry Run)
```bash
python main.py --monthly --dry-run
```
Shows what would be processed without creating files.

### Debug Mode  
```bash
python main.py --monthly --log-level DEBUG
```
Provides detailed processing information for troubleshooting.

### Custom Directory
```bash
python main.py --monthly --input-dir "/path/to/bdo/files"
```
Process files from different location.

## Success Indicators

✅ **Clear month detection**: Lists all unprocessed months found  
✅ **File processing status**: Shows transactions processed per file  
✅ **Combined output created**: Confirms monthly file generation  
✅ **Summary statistics**: Total months and transactions processed  
✅ **No errors in logs**: Processing completed successfully  

## Streamlined Monthly Routine 

**Total time: ~3 minutes**

1. **📥 Download** → Save BDO statements to Google Drive folder (1 min)
2. **⚡ Process** → Run `python main.py --monthly` (30 seconds)  
3. **📊 Import** → Import generated monthly files to accounting software (1 min)
4. **✅ Done!** → All months processed and ready for accounting

## Key Benefits of v2.0

- **🎯 Zero Configuration**: No month selection or confirmations needed
- **🔄 Batch Processing**: Handles multiple missed months automatically  
- **📁 Simplified Output**: One file per month instead of per account
- **🧠 Smart Detection**: Never processes the same data twice
- **🛡️ Robust Handling**: Adapts to BDO's changing CSV formats
- **⚡ Fast Processing**: Handles years of data in seconds

## Support

**For issues:**
- Check logs: `logs/bdo_processor.log`
- Run debug mode: `python main.py --monthly --log-level DEBUG`
- Verify file naming follows pattern
- Ensure files aren't corrupted or empty

---
*The v2.0 monthly workflow makes BDO statement processing completely automated and reliable.*