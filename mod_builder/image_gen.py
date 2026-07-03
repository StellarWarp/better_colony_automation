from __future__ import annotations

from collections import deque
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from game_paths import GAME_ROOT
from image_tools import resize_dds_batch, save_dds


MOD_ROOT = Path(__file__).resolve().parents[1]
SUPPORT_SOURCE_DIR = Path(__file__).resolve().parent / "assets" / "bca_support"
SUPPORT_OUTPUT_DIR = MOD_ROOT / "gfx" / "interface" / "bca_support"
SUPPORT_LAYOUT_CONFIG = (
    Path(__file__).resolve().parent
    / "templates"
    / "generated_configs"
    / "support_layout.yaml"
)


def load_support_layout() -> dict:
    with SUPPORT_LAYOUT_CONFIG.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    layout = config.get("support_layout") or {}
    required_keys = ["panel_size", "inner_padding"]
    missing = [key for key in required_keys if key not in layout]
    if missing:
        raise ValueError(
            f"{SUPPORT_LAYOUT_CONFIG} missing support_layout keys: {', '.join(missing)}"
        )
    return layout


def load_support_image_style() -> dict:
    with SUPPORT_LAYOUT_CONFIG.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    style = {
        "reaction_postprocess": False,
        "remove_white_background": True,
        "panel_background": True,
        "scanlines": True,
        "inner_frame": True,
        "glow_strength": 0.2,
        "saturation": 0.78,
        "brightness": 0.9,
        "contrast": 1.08,
        "tint_color": [23, 58, 52],
        "tint_strength": 0.1,
        "qr_threshold": 168,
    }
    style.update(config.get("support_image_style") or {})
    return style


SUPPORT_LAYOUT = load_support_layout()
SUPPORT_IMAGE_STYLE = load_support_image_style()
SUPPORT_IMAGE_SIZE = (
    SUPPORT_LAYOUT["panel_size"] - SUPPORT_LAYOUT["inner_padding"] * 2
)


def make_support_panel_background(size: int) -> Image.Image:
    image = Image.new("RGB", (size, size), (5, 15, 13))
    pixels = image.load()
    center = (size - 1) / 2
    max_distance = (center * center * 2) ** 0.5

    for y in range(size):
        vertical = y / max(size - 1, 1)
        for x in range(size):
            distance = (((x - center) ** 2 + (y - center) ** 2) ** 0.5) / max_distance
            glow = max(0.0, 1.0 - distance * 1.45)
            r = int(5 + glow * 8 + vertical * 3)
            g = int(15 + glow * 18 + vertical * 4)
            b = int(13 + glow * 15 + vertical * 3)
            pixels[x, y] = (r, g, b)

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    if SUPPORT_IMAGE_STYLE["scanlines"]:
        for y in range(0, size, 4):
            draw.line((0, y, size, y), fill=(0, 0, 0, 18))
    if SUPPORT_IMAGE_STYLE["inner_frame"]:
        draw.rectangle((0, 0, size - 1, size - 1), outline=(38, 116, 102, 120))
        draw.rectangle((2, 2, size - 3, size - 3), outline=(8, 36, 32, 120))
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def is_near_white(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    if a == 0:
        return True
    return r >= 226 and g >= 222 and b >= 214 and max(r, g, b) - min(r, g, b) <= 36


def remove_connected_white_background(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    source = rgba.load()
    visited: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or not (0 <= x < width and 0 <= y < height):
            continue
        if not is_near_white(source[x, y]):
            continue
        visited.add((x, y))
        queue.append((x + 1, y))
        queue.append((x - 1, y))
        queue.append((x, y + 1))
        queue.append((x, y - 1))

    alpha = rgba.getchannel("A")
    alpha_pixels = alpha.load()
    for x, y in visited:
        alpha_pixels[x, y] = 0
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.55))
    rgba.putalpha(alpha)

    return rgba


def grade_support_art(image: Image.Image) -> Image.Image:
    graded = ImageEnhance.Color(image).enhance(SUPPORT_IMAGE_STYLE["saturation"])
    graded = ImageEnhance.Brightness(graded).enhance(SUPPORT_IMAGE_STYLE["brightness"])
    graded = ImageEnhance.Contrast(graded).enhance(SUPPORT_IMAGE_STYLE["contrast"])
    tint_strength = SUPPORT_IMAGE_STYLE["tint_strength"]
    if tint_strength <= 0:
        return graded
    tint = Image.new("RGB", graded.size, tuple(SUPPORT_IMAGE_STYLE["tint_color"]))
    return Image.blend(graded, tint, tint_strength)


def fit_image(image: Image.Image, max_size: int, *, resample: Image.Resampling) -> Image.Image:
    fitted = image.copy()
    fitted.thumbnail((max_size, max_size), resample)
    return fitted


def composite_support_art(foreground: Image.Image) -> Image.Image:
    if SUPPORT_IMAGE_STYLE["panel_background"]:
        panel = make_support_panel_background(SUPPORT_IMAGE_SIZE).convert("RGBA")
    else:
        panel = Image.new("RGBA", (SUPPORT_IMAGE_SIZE, SUPPORT_IMAGE_SIZE), (0, 0, 0, 0))
    fitted = fit_image(
        foreground.convert("RGBA"),
        SUPPORT_IMAGE_SIZE,
        resample=Image.Resampling.LANCZOS,
    )
    offset = (
        (SUPPORT_IMAGE_SIZE - fitted.width) // 2,
        (SUPPORT_IMAGE_SIZE - fitted.height) // 2,
    )

    alpha_layer = Image.new("L", panel.size, 0)
    alpha_layer.paste(fitted.getchannel("A"), offset)
    glow_alpha = alpha_layer.filter(ImageFilter.MaxFilter(5)).filter(
        ImageFilter.GaussianBlur(2.2)
    )
    glow_strength = SUPPORT_IMAGE_STYLE["glow_strength"]
    if glow_strength > 0:
        glow_alpha = glow_alpha.point(lambda value: int(value * glow_strength))
        glow = Image.new("RGBA", panel.size, (48, 165, 145, 0))
        glow.putalpha(glow_alpha)
        panel = Image.alpha_composite(panel, glow)
    panel.alpha_composite(fitted, offset)
    return grade_support_art(panel.convert("RGB"))


def stylize_reaction_image(source: Path) -> Image.Image:
    if not SUPPORT_IMAGE_STYLE["reaction_postprocess"]:
        with Image.open(source) as img:
            return img.convert("RGB").resize(
                (SUPPORT_IMAGE_SIZE, SUPPORT_IMAGE_SIZE),
                Image.Resampling.LANCZOS,
            )

    with Image.open(source) as img:
        if SUPPORT_IMAGE_STYLE["remove_white_background"]:
            foreground = remove_connected_white_background(img)
        else:
            foreground = img.convert("RGBA")
    return composite_support_art(foreground)


def stylize_qr_image(source: Path) -> Image.Image:
    with Image.open(source) as img:
        qr = fit_image(
            img.convert("L"),
            SUPPORT_IMAGE_SIZE,
            resample=Image.Resampling.LANCZOS,
        )
    threshold = SUPPORT_IMAGE_STYLE["qr_threshold"]
    qr = qr.point(lambda value: 255 if value >= threshold else 0)
    dark = Image.new("RGB", qr.size, (4, 13, 11))
    light = Image.new("RGB", qr.size, (207, 223, 216))
    qr_rgb = Image.composite(light, dark, qr)

    if SUPPORT_IMAGE_STYLE["panel_background"]:
        panel = make_support_panel_background(SUPPORT_IMAGE_SIZE)
    else:
        panel = Image.new("RGB", (SUPPORT_IMAGE_SIZE, SUPPORT_IMAGE_SIZE), (207, 223, 216))
    panel.paste(
        qr_rgb,
        (
            (SUPPORT_IMAGE_SIZE - qr_rgb.width) // 2,
            (SUPPORT_IMAGE_SIZE - qr_rgb.height) // 2,
        ),
    )
    return grade_support_art(panel)


def build_qr_dds(source: Path, output: Path) -> None:
    save_dds(stylize_qr_image(source), output, relative_root=MOD_ROOT)


def build_reaction_dds(source: Path, output: Path) -> None:
    save_dds(stylize_reaction_image(source), output, relative_root=MOD_ROOT)


def build_support_assets() -> None:
    build_qr_dds(
        SUPPORT_SOURCE_DIR / "qrcode_ifdian.net.png",
        SUPPORT_OUTPUT_DIR / "qrcode_ifdian.dds",
    )
    build_qr_dds(
        SUPPORT_SOURCE_DIR / "qrcode_www.patreon.com.png",
        SUPPORT_OUTPUT_DIR / "qrcode_patreon.dds",
    )
    build_qr_dds(
        SUPPORT_SOURCE_DIR / "pay.jpg",
        SUPPORT_OUTPUT_DIR / "qrcode_alipay.dds",
    )

    build_reaction_dds(
        SUPPORT_SOURCE_DIR / "1.png",
        SUPPORT_OUTPUT_DIR / "unity_hiss.dds",
    )
    build_reaction_dds(
        SUPPORT_SOURCE_DIR / "2.png",
        SUPPORT_OUTPUT_DIR / "unity_headpat.dds",
    )
    build_reaction_dds(
        SUPPORT_SOURCE_DIR / "3.png",
        SUPPORT_OUTPUT_DIR / "unity_pitiful.dds",
    )
    build_reaction_dds(
        SUPPORT_SOURCE_DIR / "4.png",
        SUPPORT_OUTPUT_DIR / "platform_thanks.dds",
    )


def main() -> None:
    resize_dds_batch(
        GAME_ROOT
        / "gfx"
        / "interface"
        / "icons"
        / "districts"
        / "district_specialization_icons",
        MOD_ROOT / "gfx" / "interface" / "bca_districts" / "large",
        length=50,
    )
    resize_dds_batch(
        GAME_ROOT
        / "gfx"
        / "interface"
        / "icons"
        / "districts"
        / "district_specialization_icons",
        MOD_ROOT / "gfx" / "interface" / "bca_districts" / "small",
        length=25,
    )
    build_support_assets()


if __name__ == "__main__":
    main()
