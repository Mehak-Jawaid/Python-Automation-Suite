"""PDF Merger — combine multiple PDF files into one."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge multiple PDF files into a single PDF.",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="PDF files to merge, in order",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output PDF path (default: merged.pdf)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    return parser.parse_args(argv)


def validate_pdf(path: Path) -> Path:
    """Return a resolved PDF path or raise ValueError."""
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise ValueError(f"File not found: {path}")
    if not resolved.is_file():
        raise ValueError(f"Not a file: {path}")
    if resolved.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF: {path}")
    return resolved


def normalize_output(path: Path) -> Path:
    if path.suffix.lower() != ".pdf":
        path = path.with_suffix(".pdf")
    return path.expanduser().resolve()


def prompt_inputs() -> list[Path]:
    print("Enter PDF paths one per line (empty line when done):\n")
    files: list[Path] = []
    while True:
        raw = input(f"  PDF #{len(files) + 1}: ").strip().strip('"')
        if not raw:
            break
        try:
            files.append(validate_pdf(Path(raw)))
        except ValueError as exc:
            print(f"  ! {exc}")
    return files


def prompt_output(default: str = "merged.pdf") -> Path:
    raw = input(f"Output [{default}]: ").strip().strip('"')
    name = raw or default
    path = Path(name).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return normalize_output(path)


def preview(files: list[Path], output: Path) -> None:
    print("\nFiles selected:\n")
    for i, path in enumerate(files, start=1):
        print(f"{i}. {path.name}")
    print(f"\nOutput: {output.name}")
    print()


def confirm(prompt: str = "Merge PDFs? [y/n]: ") -> bool:
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}


def merge_pdfs(files: list[Path], output: Path) -> int:
    """
    Merge PDFs into output.

    Returns the total number of pages written.
    Raises OSError / PdfReadError / ValueError on failure.
    """
    if output.exists():
        raise ValueError(f"Output already exists: {output}")

    writer = PdfWriter()
    total_pages = 0

    try:
        for path in files:
            try:
                reader = PdfReader(str(path))
            except PdfReadError as exc:
                raise PdfReadError(f"Could not read {path.name}: {exc}") from exc

            if reader.is_encrypted:
                raise ValueError(f"Encrypted PDF (not supported): {path.name}")

            for page in reader.pages:
                writer.add_page(page)
                total_pages += 1

        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("wb") as fh:
            writer.write(fh)
    finally:
        writer.close()

    return total_pages


def run(
    inputs: list[Path],
    output: Path,
    *,
    skip_confirm: bool = False,
) -> int:
    if len(inputs) < 2:
        print("\nNeed at least 2 PDF files to merge.")
        return 1

    preview(inputs, output)

    if not skip_confirm and not confirm():
        print("Cancelled. No file was created.")
        return 0

    try:
        pages = merge_pdfs(inputs, output)
    except (OSError, PdfReadError, ValueError) as exc:
        print(f"\nError: {exc}")
        return 1

    print(f"\n✓ {output.name} created successfully ({pages} pages).")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    print("PDF Merger")
    print("----------")

    try:
        if args.inputs:
            inputs = [validate_pdf(Path(p)) for p in args.inputs]
            output = normalize_output(
                Path(args.output) if args.output else Path.cwd() / "merged.pdf"
            )
        else:
            print()
            inputs = prompt_inputs()
            if len(inputs) < 2:
                print("\nNeed at least 2 PDF files to merge.")
                return 1
            output = prompt_output(args.output if args.output else "merged.pdf")

        return run(inputs, output, skip_confirm=args.yes)
    except ValueError as exc:
        print(f"\nError: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
