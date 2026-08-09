# Bulk File Renamer

Rename many files in a folder with one shared prefix and automatic numbering.

**Before**

```
IMG_001.jpg
IMG_002.jpg
IMG_003.jpg
IMG_004.jpg
```

**After** (prefix `Vacation`)

```
Vacation_001.jpg
Vacation_002.jpg
Vacation_003.jpg
Vacation_004.jpg
```

## Features

- Choose a folder and naming prefix
- Rename multiple files at once
- Preserve original file extensions
- Number files automatically (`001`, `002`, …)
- Preview the rename plan before anything changes
- Confirm with `y` / `n`
- Avoid duplicate names safely (adds `_2`, `_3`, … when needed)
- Skip folders — only files in the chosen directory are renamed
- Print a summary when finished

## Requirements

- Python 3.10+ (uses built-in libraries only — no install needed)

## Usage

From this folder:

```powershell
python renamer.py
```

You will be prompted for:

1. **Folder** — path to the directory that contains the files
2. **Prefix** — new name stem (e.g. `Vacation`)
3. **Confirm** — review the preview, then type `y` to rename or `n` to cancel

### Example session

```
Python File Renamer
-------------------

Folder: C:\Users\You\Pictures
Prefix: Vacation

Preview:

  IMG_001.jpg  →  Vacation_001.jpg
  IMG_002.jpg  →  Vacation_002.jpg
  IMG_003.jpg  →  Vacation_003.jpg

Rename these files? [y/n]: y

Summary
-------
  Renamed : 3
  Skipped : 0
  Total   : 3
```

## Notes

- Only files directly inside the folder are renamed (subfolders are ignored).
- Illegal filename characters in the prefix are removed automatically.
- If a target name already exists, the tool picks a safe alternative instead of overwriting.
