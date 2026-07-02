from __future__ import annotations

import codecs
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
LOCALISATION_DIR = ROOT_DIR / "localisation"


def normalize_localisation_encoding(
    localisation_dir: Path = LOCALISATION_DIR,
) -> tuple[int, int]:
    """Ensure every localisation file is valid UTF-8 with BOM."""
    converted_count = 0
    unchanged_count = 0

    for path in sorted(localisation_dir.rglob("*")):
        if not path.is_file():
            continue

        content = path.read_bytes()
        has_bom = content.startswith(codecs.BOM_UTF8)
        encoded_content = content[len(codecs.BOM_UTF8):] if has_bom else content

        try:
            encoded_content.decode("utf-8")
        except UnicodeDecodeError as error:
            relative_path = path.relative_to(ROOT_DIR)
            raise UnicodeError(
                f"{relative_path} is not valid UTF-8: {error}"
            ) from error

        if has_bom:
            unchanged_count += 1
            continue

        path.write_bytes(codecs.BOM_UTF8 + content)
        converted_count += 1

    print(
        "Localisation encoding: "
        f"{converted_count} converted to UTF-8 with BOM, "
        f"{unchanged_count} already valid."
    )
    return converted_count, unchanged_count


def main() -> None:
    normalize_localisation_encoding()


if __name__ == "__main__":
    main()
