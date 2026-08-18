"""CSV Cleaner — trim spaces, drop duplicates, normalize headers, flag empty cells."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean a CSV: trim spaces, remove duplicates, normalize headers.",
    )
    parser.add_argument("input", nargs="?", help="CSV file to clean")
    parser.add_argument(
        "-o",
        "--output",
        help="Output CSV path (default: <name>_cleaned.csv)",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    parser.add_argument(
        "--keep-empty",
        action="store_true",
        help="Keep rows that have any empty values (still report them)",
    )
    return parser.parse_args(argv)


def validate_csv(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise ValueError(f"File not found: {path}")
    if not resolved.is_file():
        raise ValueError(f"Not a file: {path}")
    if resolved.suffix.lower() != ".csv":
        raise ValueError(f"Not a CSV: {path}")
    return resolved


def default_output(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_cleaned.csv")


def normalize_output(path: Path) -> Path:
    if path.suffix.lower() != ".csv":
        path = path.with_suffix(".csv")
    return path.expanduser().resolve()


def normalize_header(name: str) -> str:
    """Trim, collapse spaces, and Title-Case column names."""
    cleaned = re.sub(r"\s+", " ", name.strip())
    if not cleaned:
        return "Column"
    return cleaned.title()


def unique_headers(headers: list[str]) -> list[str]:
    """Ensure header names are unique (Name, Name_2, …)."""
    seen: dict[str, int] = {}
    result: list[str] = []
    for header in headers:
        count = seen.get(header, 0) + 1
        seen[header] = count
        result.append(header if count == 1 else f"{header}_{count}")
    return result


@dataclass
class CleanResult:
    headers: list[str]
    rows: list[list[str]]
    original_row_count: int
    trimmed_cells: int = 0
    duplicate_rows_removed: int = 0
    empty_rows_removed: int = 0
    empty_cells: list[tuple[int, str]] = field(default_factory=list)
    header_changes: list[tuple[str, str]] = field(default_factory=list)


def clean_csv(
    input_path: Path,
    *,
    drop_empty_rows: bool = True,
) -> CleanResult:
    with input_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        try:
            raw_headers = next(reader)
        except StopIteration as exc:
            raise ValueError("CSV is empty.") from exc

        normalized = [normalize_header(h) for h in raw_headers]
        headers = unique_headers(normalized)
        header_changes = [
            (raw, new)
            for raw, new in zip(raw_headers, headers)
            if raw != new
        ]

        result = CleanResult(
            headers=headers,
            rows=[],
            original_row_count=0,
            header_changes=header_changes,
        )

        seen: set[tuple[str, ...]] = set()

        for row_number, row in enumerate(reader, start=2):
            # Skip completely blank lines
            if not row or all(cell.strip() == "" for cell in row):
                continue

            result.original_row_count += 1

            # Pad / trim to header width
            padded = list(row) + [""] * max(0, len(headers) - len(row))
            padded = padded[: len(headers)]

            cleaned: list[str] = []
            for col_index, cell in enumerate(padded):
                trimmed = cell.strip()
                if trimmed != cell:
                    result.trimmed_cells += 1
                if trimmed == "":
                    result.empty_cells.append((row_number, headers[col_index]))
                cleaned.append(trimmed)

            if drop_empty_rows and any(cell == "" for cell in cleaned):
                result.empty_rows_removed += 1
                continue

            key = tuple(cleaned)
            if key in seen:
                result.duplicate_rows_removed += 1
                continue

            seen.add(key)
            result.rows.append(cleaned)

    return result


def write_csv(output_path: Path, headers: list[str], rows: list[list[str]]) -> None:
    if output_path.exists():
        raise ValueError(f"Output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(headers)
        writer.writerows(rows)


def preview(result: CleanResult, input_path: Path, output_path: Path) -> None:
    print(f"\nInput : {input_path}")
    print(f"Output: {output_path}")
    print()
    print("Cleaning plan:")
    print(f"  Rows read              : {result.original_row_count}")
    print(f"  Cells trimmed          : {result.trimmed_cells}")
    print(f"  Duplicate rows removed : {result.duplicate_rows_removed}")
    print(f"  Empty-value rows dropped: {result.empty_rows_removed}")
    print(f"  Rows after cleaning    : {len(result.rows)}")

    if result.header_changes:
        print("\n  Column names:")
        for raw, new in result.header_changes:
            display_raw = raw if raw.strip() else "(blank)"
            print(f"    {display_raw!r}  →  {new}")

    if result.empty_cells:
        shown = result.empty_cells[:5]
        print(f"\n  Empty values detected  : {len(result.empty_cells)}")
        for row_number, column in shown:
            print(f"    row {row_number}, column {column}")
        remaining = len(result.empty_cells) - len(shown)
        if remaining > 0:
            print(f"    … and {remaining} more")

    print("\nPreview (cleaned):")
    print("  " + ",".join(result.headers))
    for row in result.rows[:5]:
        print("  " + ",".join(row))
    if len(result.rows) > 5:
        print(f"  … ({len(result.rows) - 5} more rows)")
    print()


def confirm(prompt: str = "Save cleaned CSV? [y/n]: ") -> bool:
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}


def prompt_input() -> Path:
    raw = input("CSV file: ").strip().strip('"')
    if not raw:
        raise ValueError("No file provided.")
    return validate_csv(Path(raw))


def prompt_output(default: Path) -> Path:
    raw = input(f"Output [{default.name}]: ").strip().strip('"')
    if not raw:
        return default
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return normalize_output(path)


def run(
    input_path: Path,
    output_path: Path,
    *,
    skip_confirm: bool = False,
    drop_empty_rows: bool = True,
) -> int:
    try:
        result = clean_csv(input_path, drop_empty_rows=drop_empty_rows)
    except (OSError, UnicodeError, csv.Error) as exc:
        print(f"\nError reading CSV: {exc}")
        return 1

    preview(result, input_path, output_path)

    if not result.rows:
        print("Nothing to save — no rows remain after cleaning.")
        return 1

    if not skip_confirm and not confirm():
        print("Cancelled. No file was created.")
        return 0

    try:
        write_csv(output_path, result.headers, result.rows)
    except (OSError, ValueError) as exc:
        print(f"\nError: {exc}")
        return 1

    print(f"\nOK: {output_path.name} created successfully ({len(result.rows)} rows).")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    print("CSV Cleaner")
    print("-----------")

    try:
        if args.input:
            input_path = validate_csv(Path(args.input))
        else:
            print()
            input_path = prompt_input()

        if args.output:
            output_path = normalize_output(Path(args.output))
        elif args.input:
            output_path = default_output(input_path)
        else:
            output_path = prompt_output(default_output(input_path))

        return run(
            input_path,
            output_path,
            skip_confirm=args.yes,
            drop_empty_rows=not args.keep_empty,
        )
    except ValueError as exc:
        print(f"\nError: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
