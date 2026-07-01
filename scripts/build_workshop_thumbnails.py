from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps


ROOT_DIR = Path(__file__).resolve().parents[1]
FONT_PATH = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
OUTPUT_SIZE = 512
MAX_OUTPUT_BYTES = 900_000


@dataclass(frozen=True)
class ThumbnailSpec:
    directory: Path
    title_lines: tuple[str, ...]
    accent: tuple[int, int, int]

    @property
    def source(self) -> Path:
        return self.directory / "thumbnail_0.png"

    @property
    def output(self) -> Path:
        return self.directory / "thumbnail.png"


SPECS = {
    "main": ThumbnailSpec(
        directory=ROOT_DIR,
        title_lines=("BETTER COLONY", "AUTOMATION"),
        accent=(105, 203, 229),
    ),
    "job_regulation": ThumbnailSpec(
        directory=ROOT_DIR / "submods" / "job_regulation",
        title_lines=("MACROECONOMY", "THE VISIBLE HAND"),
        accent=(231, 181, 74),
    ),
}


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int):
    size = start_size
    while size >= 20:
        font = ImageFont.truetype(str(FONT_PATH), size)
        bounds = draw.textbbox((0, 0), text, font=font, stroke_width=1)
        if bounds[2] - bounds[0] <= max_width:
            return font
        size -= 1
    raise ValueError(f"cannot fit title text: {text}")


def add_title_overlay(image: Image.Image, spec: ThumbnailSpec) -> Image.Image:
    image = ImageEnhance.Contrast(image).enhance(1.06).convert("RGBA")
    shade = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shade_pixels = shade.load()
    for y in range(220):
        alpha = max(0, round(205 * (1 - y / 220)))
        for x in range(OUTPUT_SIZE):
            shade_pixels[x, y] = (0, 0, 0, alpha)
    image.alpha_composite(shade)

    draw = ImageDraw.Draw(image)
    max_width = OUTPUT_SIZE - 44
    title_y = 22
    line_gap = 2
    for index, text in enumerate(spec.title_lines):
        font = fit_font(draw, text, max_width, 55 if index == 0 else 48)
        bounds = draw.textbbox((0, 0), text, font=font, stroke_width=2)
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        x = (OUTPUT_SIZE - width) // 2
        draw.text(
            (x, title_y - bounds[1]),
            text,
            font=font,
            fill=(238, 244, 247, 255),
            stroke_width=2,
            stroke_fill=(4, 10, 14, 255),
        )
        title_y += height + line_gap

    line_y = title_y + 10
    line_width = 170
    draw.rounded_rectangle(
        (
            (OUTPUT_SIZE - line_width) // 2,
            line_y,
            (OUTPUT_SIZE + line_width) // 2,
            line_y + 5,
        ),
        radius=2,
        fill=(*spec.accent, 255),
    )
    return image.convert("RGB")


def save_optimized(image: Image.Image, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True, compress_level=9)
    if output.stat().st_size <= MAX_OUTPUT_BYTES:
        return
    quantized = image.quantize(
        colors=256,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.FLOYDSTEINBERG,
    )
    quantized.save(output, format="PNG", optimize=True, compress_level=9)


def build_thumbnail(spec: ThumbnailSpec) -> None:
    if not FONT_PATH.is_file():
        raise FileNotFoundError(f"font not found: {FONT_PATH}")
    if not spec.source.is_file():
        raise FileNotFoundError(f"thumbnail source not found: {spec.source}")
    with Image.open(spec.source) as source:
        fitted = ImageOps.fit(
            source.convert("RGB"),
            (OUTPUT_SIZE, OUTPUT_SIZE),
            method=Image.Resampling.LANCZOS,
        )
    result = add_title_overlay(fitted, spec)
    save_optimized(result, spec.output)
    print(
        f"{spec.output.relative_to(ROOT_DIR)}: "
        f"{OUTPUT_SIZE}x{OUTPUT_SIZE}, {spec.output.stat().st_size} bytes"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build square, upload-sized Steam Workshop thumbnails."
    )
    parser.add_argument(
        "--package",
        choices=["all", *SPECS],
        default="all",
        help="Thumbnail package to build (default: all).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    packages = SPECS if args.package == "all" else {args.package: SPECS[args.package]}
    for spec in packages.values():
        build_thumbnail(spec)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
