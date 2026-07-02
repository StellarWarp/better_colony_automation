from __future__ import annotations

from pathlib import Path

from PIL import Image


def resize_dds_batch(input_folder: Path, output_folder: Path, length: int = 50) -> None:
    output_folder.mkdir(parents=True, exist_ok=True)

    for source in input_folder.iterdir():
        if not source.is_file() or source.suffix.lower() != ".dds":
            continue
        with Image.open(source) as img:
            resized = img.resize((length, length), Image.Resampling.LANCZOS)
            resized.save(output_folder / source.name)
            print(f"Processed: {source.name} -> {(length, length)}")


def save_dds(image: Image.Image, output: Path, *, relative_root: Path | None = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="DDS")
    try:
        display_path = output.relative_to(relative_root) if relative_root else output
    except ValueError:
        display_path = output
    print(f"Generated: {display_path} {image.size}")
