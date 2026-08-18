# PDF Merger

Combine multiple PDF files into one document.

**Example**

```
PDF Merger
----------

Files selected:

1. Resume.pdf
2. CoverLetter.pdf
3. Certificates.pdf

Output: Application.pdf

Merge PDFs? [y/n]: y

OK: Application.pdf created successfully (12 pages).
```

## Features

- Merge two or more PDFs in the order you choose
- Interactive mode or command-line arguments
- Preview selected files before merging
- Confirm with `y` / `n`
- Clear errors for missing, invalid, or encrypted PDFs
- Refuses to overwrite an existing output file

## Requirements

- Python 3.10+
- [`pypdf`](https://pypi.org/project/pypdf/)

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Usage

### Interactive

```powershell
python merger.py
```

Then enter PDF paths one per line, press Enter on a blank line when finished, and choose an output name.

### Command line

```powershell
python merger.py Resume.pdf CoverLetter.pdf Certificates.pdf -o Application.pdf
```

Skip the confirmation prompt:

```powershell
python merger.py a.pdf b.pdf -o combined.pdf -y
```

| Flag | Meaning |
|------|---------|
| `-o`, `--output` | Output PDF path (default: `merged.pdf`) |
| `-y`, `--yes` | Skip confirmation |

## What you'll practice

- File handling
- Third-party Python packages (`pypdf`)
- Exceptions
- Command-line arguments (`argparse`)
