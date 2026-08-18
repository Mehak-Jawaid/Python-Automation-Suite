# CSV Cleaner

Clean messy CSV files for freelance and everyday data work.

**Input**

```csv
Name,Email,Age
John,john@email.com,25
 Mary ,mary@email.com,30
John,john@email.com,25
```

**Output**

```csv
Name,Email,Age
John,john@email.com,25
Mary,mary@email.com,30
```

## Features

- Remove duplicate rows
- Strip leading/trailing spaces
- Detect empty values (and drop those rows by default)
- Normalize column names
- Preview changes before saving
- Confirm with `y` / `n`
- Save a cleaned CSV (does not overwrite existing output)

## Requirements

- Python 3.10+ (stdlib only — no install needed)

## Usage

### Interactive

```powershell
python cleaner.py
```

### Command line

```powershell
python cleaner.py messy.csv -o clean.csv
```

Skip confirmation:

```powershell
python cleaner.py messy.csv -y
```

Keep rows that have empty cells (still reports them):

```powershell
python cleaner.py messy.csv --keep-empty -o clean.csv
```

| Flag | Meaning |
|------|---------|
| `-o`, `--output` | Output path (default: `<name>_cleaned.csv`) |
| `-y`, `--yes` | Skip confirmation |
| `--keep-empty` | Keep rows with empty values |

## Example session

```
CSV Cleaner
-----------

Input : messy.csv
Output: messy_cleaned.csv

Cleaning plan:
  Rows read              : 3
  Cells trimmed          : 1
  Duplicate rows removed : 1
  Empty-value rows dropped: 0
  Rows after cleaning    : 2

Preview (cleaned):
  Name,Email,Age
  John,john@email.com,25
  Mary,mary@email.com,30

Save cleaned CSV? [y/n]: y

OK: messy_cleaned.csv created successfully (2 rows).
```

## What you'll practice

- File handling with the `csv` module
- Data cleaning logic
- Exceptions
- Command-line arguments (`argparse`)
