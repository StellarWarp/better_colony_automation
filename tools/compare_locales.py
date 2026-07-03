from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCALISATION_DIR = ROOT / "localisation"
BASE_LANGUAGE = "simp_chinese"
DEFAULT_TARGET_LANGUAGES = ("english", "japanese", "russian")
DEFAULT_EXCLUDED_BASE_FILES = ("bca_test_l_simp_chinese.yml",)
KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*:")
HEADER_RE = re.compile(r"^\s*l_[A-Za-z_]+\s*:\s*$")


@dataclass(frozen=True)
class LocaleComparison:
    base_file: Path
    target_language: str
    target_file: Path
    missing_file: bool
    missing_keys: tuple[str, ...]
    extra_keys: tuple[str, ...]


def read_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            if HEADER_RE.match(stripped):
                continue
            match = KEY_RE.match(line)
            if match:
                keys.add(match.group(1))
    return keys


def target_path_for(base_file: Path, target_language: str) -> Path:
    relative = base_file.relative_to(LOCALISATION_DIR / BASE_LANGUAGE)
    name = relative.name.replace(
        f"_l_{BASE_LANGUAGE}.yml",
        f"_l_{target_language}.yml",
    )
    return LOCALISATION_DIR / target_language / relative.with_name(name)


def iter_base_files(excluded_names: tuple[str, ...] = DEFAULT_EXCLUDED_BASE_FILES) -> list[Path]:
    excluded = set(excluded_names)
    return sorted(
        path
        for path in (LOCALISATION_DIR / BASE_LANGUAGE).rglob("*.yml")
        if path.name not in excluded
    )


def compare_language_file(
    base_file: Path,
    base_keys: set[str],
    target_language: str,
) -> LocaleComparison:
    target_file = target_path_for(base_file, target_language)
    if not target_file.is_file():
        return LocaleComparison(
            base_file=base_file,
            target_language=target_language,
            target_file=target_file,
            missing_file=True,
            missing_keys=tuple(sorted(base_keys)),
            extra_keys=(),
        )

    target_keys = read_keys(target_file)
    return LocaleComparison(
        base_file=base_file,
        target_language=target_language,
        target_file=target_file,
        missing_file=False,
        missing_keys=tuple(sorted(base_keys - target_keys)),
        extra_keys=tuple(sorted(target_keys - base_keys)),
    )


def compare_locales(
    target_languages: tuple[str, ...],
    excluded_names: tuple[str, ...] = DEFAULT_EXCLUDED_BASE_FILES,
) -> list[LocaleComparison]:
    comparisons: list[LocaleComparison] = []
    for base_file in iter_base_files(excluded_names):
        base_keys = read_keys(base_file)
        for target_language in target_languages:
            comparisons.append(
                compare_language_file(base_file, base_keys, target_language)
            )
    return comparisons


def print_comparison(comparison: LocaleComparison) -> None:
    base_display = comparison.base_file.relative_to(ROOT)
    target_display = comparison.target_file.relative_to(ROOT)
    if (
        not comparison.missing_file
        and not comparison.missing_keys
        and not comparison.extra_keys
    ):
        return

    print(f"FILE: {base_display}")
    print(f"  Target: {comparison.target_language} ({target_display})")
    if comparison.missing_file:
        print("  Missing file")
    print(f"  Missing keys: {len(comparison.missing_keys)}")
    for key in comparison.missing_keys:
        print(f"    - {key}")
    print(f"  Extra keys: {len(comparison.extra_keys)}")
    for key in comparison.extra_keys:
        print(f"    + {key}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare Stellaris localisation keys against simp_chinese as the "
            "baseline."
        )
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=list(DEFAULT_TARGET_LANGUAGES),
        help="Target language directories to compare against simp_chinese.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print the final summary.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with a non-zero status when differences are found.",
    )
    parser.add_argument(
        "--include-tests",
        action="store_true",
        help="Include test/debug localisation files in the comparison.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target_languages = tuple(args.languages)
    excluded_names = () if args.include_tests else DEFAULT_EXCLUDED_BASE_FILES
    comparisons = compare_locales(target_languages, excluded_names)

    if not args.quiet:
        for comparison in comparisons:
            print_comparison(comparison)

    total_base_files = len(iter_base_files(excluded_names))
    total_missing_files = sum(1 for item in comparisons if item.missing_file)
    total_missing_keys = sum(len(item.missing_keys) for item in comparisons)
    total_extra_keys = sum(len(item.extra_keys) for item in comparisons)
    print(f"SUMMARY: base language: {BASE_LANGUAGE}")
    print(f"SUMMARY: base files scanned: {total_base_files}")
    print(f"SUMMARY: target languages: {', '.join(target_languages)}")
    print(f"SUMMARY: missing files: {total_missing_files}")
    print(f"SUMMARY: missing keys: {total_missing_keys}")
    print(f"SUMMARY: extra keys: {total_extra_keys}")

    has_differences = bool(total_missing_files or total_missing_keys or total_extra_keys)
    return 1 if args.strict and has_differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
