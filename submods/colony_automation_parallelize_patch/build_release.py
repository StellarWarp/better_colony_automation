from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "src" / "automation_queue_capacity_patcher.py"
TESTS = ROOT / "tests"
BUILD = ROOT / "build"
DIST = ROOT / "dist"
EXECUTABLE = DIST / "ColonyAutomationParallelizePatch.exe"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def build(*, skip_tests: bool) -> Path:
    if not skip_tests:
        run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(TESTS),
                "-p",
                "test_*.py",
                "-v",
            ]
        )
    if BUILD.exists():
        shutil.rmtree(BUILD)
    DIST.mkdir(parents=True, exist_ok=True)
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onefile",
            "--console",
            "--name",
            "ColonyAutomationParallelizePatch",
            "--distpath",
            str(DIST),
            "--workpath",
            str(BUILD / "work"),
            "--specpath",
            str(BUILD),
            str(SOURCE),
        ]
    )
    if not EXECUTABLE.is_file():
        raise FileNotFoundError(f"build did not produce {EXECUTABLE}")
    run([str(EXECUTABLE), "--help"])
    print(f"Built {EXECUTABLE} ({EXECUTABLE.stat().st_size} bytes)")
    return EXECUTABLE


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the standalone patcher.")
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    try:
        build(skip_tests=args.skip_tests)
        return 0
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"build failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
