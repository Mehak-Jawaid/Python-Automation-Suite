# Image Resizer

Batch-resize every image in a folder to a target width and height.

**Example**

```
Image Resizer
-------------

Input folder: images/
Width: 800
Height: 600

Processing...

OK: image1.jpg
OK: image2.jpg
OK: image3.jpg

3 images resized successfully.
```

## Features

- Choose an input folder, width, and height
- Resize many images in one run (batch processing)
- Save to a separate output folder (default: `<folder>/resized`) so originals stay safe
- Optional `--keep-aspect` to fit inside the box without stretching
- Preview + confirm before processing
- Per-file success/failure reporting
- Clear errors for bad or unreadable files

## Requirements

- Python 3.10+
- [`Pillow`](https://pypi.org/project/Pillow/)

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Supported formats

`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.gif`, `.tif`, `.tiff`

## Usage

### Interactive

```powershell
python resizer.py
```

### Command line

```powershell
python resizer.py images -W 800 -H 600 -o images/resized
```

Keep aspect ratio (fit inside 800×600):

```powershell
python resizer.py images -W 800 -H 600 --keep-aspect -y
```

| Flag | Meaning |
|------|---------|
| `-W`, `--width` | Target width in pixels |
| `-H`, `--height` | Target height in pixels |
| `-o`, `--output` | Output folder (default: `<folder>/resized`) |
| `--keep-aspect` | Fit inside the box without stretching |
| `-y`, `--yes` | Skip confirmation |

## What you'll practice

- Working with images (`Pillow`)
- File paths (`pathlib`)
- Batch processing
- Error handling
