from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "assets" / "construction_queue.png"
OUTPUT = ROOT / "thumbnail.png"
FONT = Path(r"C:\Windows\Fonts\bahnschrift.ttf")
SIZE = 512


def fitted_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, size: int):
    while size >= 18:
        font = ImageFont.truetype(str(FONT), size)
        box = draw.textbbox((0, 0), text, font=font)
        if box[2] - box[0] <= max_width:
            return font
        size -= 1
    raise ValueError(f"cannot fit text: {text}")


def centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    *,
    size: int,
    fill: tuple[int, int, int],
) -> None:
    font = fitted_font(draw, text, SIZE - 48, size)
    box = draw.textbbox((0, 0), text, font=font)
    width = box[2] - box[0]
    draw.text(((SIZE - width) // 2, y - box[1]), text, font=font, fill=fill)


def build() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    if not FONT.is_file():
        raise FileNotFoundError(FONT)

    canvas = Image.new("RGB", (SIZE, SIZE), (5, 12, 11))
    draw = ImageDraw.Draw(canvas)

    centered_text(
        draw,
        "COLONY AUTOMATION",
        16,
        size=26,
        fill=(139, 168, 159),
    )
    centered_text(
        draw,
        "PARALLEL BUILD FIX",
        48,
        size=43,
        fill=(232, 240, 237),
    )

    with Image.open(SOURCE) as source:
        source = source.convert("RGB")
        queue_crop = source.crop((12, 130, 476, 600))
        queue_crop = ImageEnhance.Contrast(queue_crop).enhance(1.08)
        queue_crop = ImageEnhance.Brightness(queue_crop).enhance(0.92)
        panel = ImageOps.fit(
            queue_crop,
            (400, 380),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.0),
        )

    panel_width, panel_height = panel.size
    panel_x = (SIZE - panel_width) // 2
    panel_y = 108
    canvas.paste(panel, (panel_x, panel_y))
    draw.rectangle(
        (
            panel_x - 2,
            panel_y - 2,
            panel_x + panel_width + 1,
            panel_y + panel_height + 1,
        ),
        outline=(56, 153, 132),
        width=2,
    )
    draw.rectangle(
        (8, 8, SIZE - 9, SIZE - 9),
        outline=(28, 66, 59),
        width=1,
    )

    canvas.save(OUTPUT, format="PNG", optimize=True, compress_level=9)
    if OUTPUT.stat().st_size > 900_000:
        raise ValueError(f"thumbnail exceeds Workshop size budget: {OUTPUT.stat().st_size}")
    print(f"{OUTPUT}: {SIZE}x{SIZE}, {OUTPUT.stat().st_size} bytes")


if __name__ == "__main__":
    build()
