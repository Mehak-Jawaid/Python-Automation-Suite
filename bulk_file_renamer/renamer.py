"""Bulk File Renamer — rename files in a folder with a shared prefix and numbering."""

from __future__ import annotations

import re
from pathlib import Path


def list_files(folder: Path) -> list[Path]:
    """Return files in folder only (no subdirectories), sorted by name."""
    return sorted(
        (p for p in folder.iterdir() if p.is_file()),
        key=lambda p: p.name.lower(),
    )


def build_rename_plan(
    files: list[Path],
    prefix: str,
    start: int = 1,
) -> list[tuple[Path, Path]]:
    """
    Build (source, destination) pairs.

    Numbering width matches the file count (e.g. 4 files → 001…004).
    Duplicate destinations are avoided by appending _2, _3, etc.
    """
    if not files:
        return []

    width = max(3, len(str(start + len(files) - 1)))
    planned: list[tuple[Path, Path]] = []
    claimed: set[str] = set()

    # Existing names that will remain after renames (not in our rename set)
    sources = {f.resolve() for f in files}
    for path in files[0].parent.iterdir():
        if path.is_file() and path.resolve() not in sources:
            claimed.add(path.name.lower())

    for index, source in enumerate(files, start=start):
        stem = f"{prefix}_{index:0{width}d}"
        ext = source.suffix
        candidate = f"{stem}{ext}"

        # Skip if the name is already taken or already planned
        if candidate.lower() in claimed or any(
            dest.name.lower() == candidate.lower() for _, dest in planned
        ):
            n = 2
            while True:
                candidate = f"{stem}_{n}{ext}"
                if candidate.lower() not in claimed and not any(
                    dest.name.lower() == candidate.lower() for _, dest in planned
                ):
                    break
                n += 1

        dest = source.with_name(candidate)
        planned.append((source, dest))
        claimed.add(candidate.lower())

    return planned


def preview(plan: list[tuple[Path, Path]]) -> None:
    print("\nPreview:\n")
    if not plan:
        print("  (no files to rename)")
        return
    for source, dest in plan:
        if source.name == dest.name:
            print(f"  {source.name}  →  (unchanged)")
        else:
            print(f"  {source.name}  →  {dest.name}")
    print()


def confirm(prompt: str = "Rename these files? [y/n]: ") -> bool:
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}


def apply_renames(plan: list[tuple[Path, Path]]) -> tuple[int, int, list[str]]:
    """
    Rename files using a two-pass approach so intermediate collisions
    (A→B while B→C) do not overwrite each other.
    """
    renamed = 0
    skipped = 0
    errors: list[str] = []

    # Only rename when the name actually changes
    changes = [(src, dst) for src, dst in plan if src.name != dst.name]
    if not changes:
        return 0, len(plan), errors

    folder = changes[0][0].parent
    temps: list[tuple[Path, Path, Path]] = []  # (original, temp, final)

    # Pass 1: move everything to unique temp names
    for i, (src, dst) in enumerate(changes):
        temp = folder / f".renamer_tmp_{i}_{src.name}"
        try:
            src.rename(temp)
            temps.append((src, temp, dst))
        except OSError as exc:
            errors.append(f"{src.name}: {exc}")
            skipped += 1

    # Pass 2: move temps to final names; resolve last-moment collisions
    for original, temp, dst in temps:
        final = dst
        if final.exists():
            stem = final.stem
            # If stem already ends with _N from our earlier suffixing, bump further
            base_match = re.match(r"^(.*?)(?:_(\d+))?$", stem)
            base = base_match.group(1) if base_match else stem
            n = 2
            while True:
                candidate = final.with_name(f"{base}_{n}{final.suffix}")
                if not candidate.exists():
                    final = candidate
                    break
                n += 1

        try:
            temp.rename(final)
            renamed += 1
        except OSError as exc:
            # Try to restore original name
            try:
                temp.rename(original)
            except OSError:
                pass
            errors.append(f"{original.name}: {exc}")
            skipped += 1

    return renamed, skipped, errors


def prompt_folder() -> Path | None:
    raw = input("Folder: ").strip().strip('"')
    if not raw:
        print("No folder provided.")
        return None
    folder = Path(raw).expanduser()
    if not folder.exists():
        print(f"Folder does not exist: {folder}")
        return None
    if not folder.is_dir():
        print(f"Not a directory: {folder}")
        return None
    return folder.resolve()


def prompt_prefix() -> str | None:
    prefix = input("Prefix: ").strip()
    if not prefix:
        print("Prefix cannot be empty.")
        return None
    # Strip characters that are illegal in Windows filenames
    cleaned = re.sub(r'[<>:"/\\|?*]', "", prefix).rstrip(" .")
    if not cleaned:
        print("Prefix is invalid after removing illegal characters.")
        return None
    if cleaned != prefix:
        print(f"Using sanitized prefix: {cleaned}")
    return cleaned


def main() -> None:
    print("Python File Renamer")
    print("-------------------")
    print()

    folder = prompt_folder()
    if folder is None:
        return

    prefix = prompt_prefix()
    if prefix is None:
        return

    files = list_files(folder)
    if not files:
        print(f"\nNo files found in {folder}")
        return

    plan = build_rename_plan(files, prefix)
    print(f"\nFolder: {folder}")
    print(f"Prefix: {prefix}")
    preview(plan)

    to_change = sum(1 for src, dst in plan if src.name != dst.name)
    if to_change == 0:
        print("Nothing to rename — names already match the plan.")
        return

    if not confirm():
        print("Cancelled. No files were renamed.")
        return

    renamed, skipped, errors = apply_renames(plan)

    print("\nSummary")
    print("-------")
    print(f"  Renamed : {renamed}")
    print(f"  Skipped : {skipped}")
    print(f"  Total   : {len(plan)}")
    if errors:
        print("\nErrors:")
        for msg in errors:
            print(f"  - {msg}")


if __name__ == "__main__":
    main()
