"""Re-encode vanilla job icons into this mod so GUI text icons use local assets."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from game_paths import GAME_ROOT


MOD_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = GAME_ROOT / "gfx" / "interface" / "icons" / "jobs"
TARGET_DIR = MOD_ROOT / "gfx" / "interface" / "bca_jobs"


def sync_job_icons() -> None:
    if not SOURCE_DIR.is_dir():
        raise FileNotFoundError(f"Stellaris job icon directory not found: {SOURCE_DIR}")

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    converted = 0
    failed: list[tuple[str, str]] = []
    for source in SOURCE_DIR.iterdir():
        if not source.is_file() or source.suffix.lower() != ".dds":
            continue
        target = TARGET_DIR / source.name
        try:
            with Image.open(source) as img:
                img.save(target)
            converted += 1
        except Exception as exc:
            failed.append((source.name, str(exc)))

    print(f"Re-encoded {converted} job icon files to {TARGET_DIR}")
    if failed:
        print(f"Failed to re-encode {len(failed)} job icon files:")
        for filename, error in failed:
            print(f"  {filename}: {error}")
        raise RuntimeError("Some job icons failed to re-encode")


def main() -> None:
    sync_job_icons()


if __name__ == "__main__":
    main()
