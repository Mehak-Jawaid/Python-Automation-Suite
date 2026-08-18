"""Image Resizer — batch-resize images in a folder to a target size."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resize all images in a folder to a target width and height.",
    )
    parser.add_argument(
        "folder",
        nargs="?",
        help="Folder containing images",
    )
    parser.add_argument(
        "-W",
        "--width",
        type=int,
        help="Target width in pixels",
    )
    parser.add_argument(
        "-H",
        "--height",
        type=int,
        help="Target height in pixels",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output folder (default: <folder>/resized)",
    )
    parser.add_argument(
        "--keep-aspect",
        action="store_true",
        help="Fit inside width x height without cropping or stretching",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt",
    )
    return parser.parse_args(argv)


def validate_folder(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise ValueError(f"Folder does not exist: {path}")
    if not resolved.is_dir():
        raise ValueError(f"Not a directory: {path}")
    return resolved


def validate_size(value: int, label: str) -> int:
    if value < 1:
        raise ValueError(f"{label} must be at least 1.")
    if value > 10000:
        raise ValueError(f"{label} is too large (max 10000).")
    return value


def list_images(folder: Path) -> list[Path]:
    return sorted(
        (
            p
            for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
        ),
        key=lambda p: p.name.lower(),
    )


def default_output(folder: Path) -> Path:
    return folder / "resized"


def prompt_folder() -> Path:
    raw = input("Input folder: ").strip().strip('"')
    if not raw:
        raise ValueError("No folder provided.")
    return validate_folder(Path(raw))


def prompt_int(label: str) -> int:
    raw = input(f"{label}: ").strip()
    if not raw:
        raise ValueError(f"{label} is required.")
    try:
        return validate_size(int(raw), label)
    except ValueError as exc:
        if "invalid literal" in str(exc).lower():
            raise ValueError(f"{label} must be a whole number.") from exc
        raise


def prompt_output(default: Path) -> Path:
    raw = input(f"Output folder [{default}]: ").strip().strip('"')
    if not raw:
        return default
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def preview(
    images: list[Path],
    folder: Path,
    output: Path,
    width: int,
    height: int,
    keep_aspect: bool,
) -> None:
    print(f"\nInput folder: {folder}")
    print(f"Output folder: {output}")
    print(f"Width: {width}")
    print(f"Height: {height}")
    print(f"Keep aspect: {'yes' if keep_aspect else 'no'}")
    print(f"\nImages found: {len(images)}")
    for path in images[:8]:
        print(f"  - {path.name}")
    if len(images) > 8:
        print(f"  … and {len(images) - 8} more")
    print()


def confirm(prompt: str = "Resize these images? [y/n]: ") -> bool:
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}


def resize_image(
    source: Path,
    destination: Path,
    width: int,
    height: int,
    *,
    keep_aspect: bool,
) -> None:
    with Image.open(source) as img:
        # Convert palette / weird modes so JPEG saves cleanly when needed
        working = img
        if working.mode not in {"RGB", "RGBA", "L"}:
            working = working.convert("RGB")

        if keep_aspect:
            fitted = working.copy()
            fitted.thumbnail((width, height), Image.Resampling.LANCZOS)
            resized = fitted
        else:
            resized = working.resize((width, height), Image.Resampling.LANCZOS)

        destination.parent.mkdir(parents=True, exist_ok=True)

        save_kwargs: dict = {}
        suffix = destination.suffix.lower()
        if suffix in {".jpg", ".jpeg"}:
            if resized.mode == "RGBA":
                resized = resized.convert("RGB")
            save_kwargs["quality"] = 90
            save_kwargs["optimize"] = True

        resized.save(destination, **save_kwargs)


def process_images(
    images: list[Path],
    output: Path,
    width: int,
    height: int,
    *,
    keep_aspect: bool,
) -> tuple[int, list[str]]:
    print("Processing...\n")
    ok = 0
    errors: list[str] = []

    for source in images:
        dest = output / source.name
        try:
            if dest.resolve() == source.resolve():
                raise ValueError("output path would overwrite the original")
            resize_image(
                source,
                dest,
                width,
                height,
                keep_aspect=keep_aspect,
            )
            print(f"OK: {source.name}")
            ok += 1
        except (OSError, UnidentifiedImageError, ValueError) as exc:
            message = f"{source.name}: {exc}"
            print(f"FAIL: {message}")
            errors.append(message)

    return ok, errors


def run(
    folder: Path,
    output: Path,
    width: int,
    height: int,
    *,
    keep_aspect: bool = False,
    skip_confirm: bool = False,
) -> int:
    images = list_images(folder)
    if not images:
        print(f"\nNo images found in {folder}")
        print(f"Supported types: {', '.join(sorted(IMAGE_EXTENSIONS))}")
        return 1

    if output.resolve() == folder.resolve():
        print("\nError: output folder must be different from the input folder.")
        return 1

    preview(images, folder, output, width, height, keep_aspect)

    if not skip_confirm and not confirm():
        print("Cancelled. No images were resized.")
        return 0

    ok, errors = process_images(
        images,
        output,
        width,
        height,
        keep_aspect=keep_aspect,
    )

    print()
    if ok:
        print(f"{ok} image{'s' if ok != 1 else ''} resized successfully.")
    if errors:
        print(f"{len(errors)} failed:")
        for message in errors:
            print(f"  - {message}")
        return 1 if ok == 0 else 0
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    print("Image Resizer")
    print("-------------")

    try:
        if args.folder:
            folder = validate_folder(Path(args.folder))
        else:
            print()
            folder = prompt_folder()

        if args.width is not None:
            width = validate_size(args.width, "Width")
        else:
            width = prompt_int("Width")

        if args.height is not None:
            height = validate_size(args.height, "Height")
        else:
            height = prompt_int("Height")

        if args.output:
            output = Path(args.output).expanduser()
            if not output.is_absolute():
                output = Path.cwd() / output
            output = output.resolve()
        elif args.folder:
            output = default_output(folder)
        else:
            output = prompt_output(default_output(folder))

        return run(
            folder,
            output,
            width,
            height,
            keep_aspect=args.keep_aspect,
            skip_confirm=args.yes,
        )
    except ValueError as exc:
        print(f"\nError: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
