from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = Path(__file__).with_suffix(".yaml")
PUBLISH_METADATA_RE = re.compile(
    r"^#\s*submod\s+(?P<name>[A-Za-z0-9_.-]+)"
    r"(?:\s+file_name\s+(?P<file_name>[^\s]+))?\s*$"
)
METADATA_EXTENSIONS = {".txt", ".gui", ".gfx", ".yml"}


@dataclass(frozen=True)
class PublishMetadata:
    submod: str | None = None
    file_name: str | None = None


@dataclass(frozen=True)
class PublishItem:
    source: Path
    destination: Path
    relative_destination: Path
    package: str


def expand_path(raw_path: str, *, base: Path) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(raw_path))
    path = Path(expanded)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}
    if "main" not in config:
        raise ValueError("publish config must define main")
    if not config.get("source_directories"):
        raise ValueError("publish config must define source_directories")
    return config


def read_publish_metadata(path: Path) -> PublishMetadata:
    if path.suffix.lower() not in METADATA_EXTENSIONS:
        return PublishMetadata()
    with path.open("r", encoding="utf-8-sig", errors="ignore") as source_file:
        first_line = source_file.readline().rstrip("\r\n")
    match = PUBLISH_METADATA_RE.fullmatch(first_line)
    if not match:
        return PublishMetadata()
    file_name = match.group("file_name")
    if file_name and Path(file_name).name != file_name:
        raise ValueError(f"{path}: file_name must be a basename")
    return PublishMetadata(
        submod=match.group("name"),
        file_name=file_name,
    )


def package_configs(config: dict, *, base: Path) -> dict[str, dict]:
    packages = {"main": dict(config["main"])}
    packages.update(
        {name: dict(value) for name, value in (config.get("submods") or {}).items()}
    )
    for name, package in packages.items():
        if not package.get("target"):
            raise ValueError(f"package {name} has no target")
        package["target_path"] = expand_path(package["target"], base=base)
    targets = [package["target_path"] for package in packages.values()]
    if len(set(targets)) != len(targets):
        raise ValueError("publish targets must be unique")
    for target in targets:
        if target == ROOT_DIR or ROOT_DIR in target.parents:
            raise ValueError(f"publish target cannot be inside the repository: {target}")
        filesystem_root = Path(target.anchor).resolve()
        if target in {filesystem_root, Path.home().resolve()}:
            raise ValueError(f"publish target is too broad to replace: {target}")
    return packages


def add_item(
    items: list[PublishItem],
    destinations: dict[Path, Path],
    *,
    source: Path,
    target: Path,
    relative_destination: Path,
    package: str,
) -> None:
    destination = (target / relative_destination).resolve()
    if target != destination and target not in destination.parents:
        raise ValueError(f"refusing destination outside target: {destination}")
    previous_source = destinations.get(destination)
    if previous_source is not None:
        raise ValueError(
            f"duplicate publish destination {destination}: "
            f"{previous_source} and {source}"
        )
    destinations[destination] = source
    items.append(
        PublishItem(
            source=source,
            destination=destination,
            relative_destination=relative_destination,
            package=package,
        )
    )


def collect_publish_items(config: dict, packages: dict[str, dict]) -> list[PublishItem]:
    items: list[PublishItem] = []
    destinations: dict[Path, Path] = {}

    for directory_name in config["source_directories"]:
        source_directory = (ROOT_DIR / directory_name).resolve()
        if not source_directory.is_dir():
            raise FileNotFoundError(f"source directory does not exist: {source_directory}")
        for source in sorted(source_directory.rglob("*")):
            if not source.is_file():
                continue
            metadata = read_publish_metadata(source)
            package_name = metadata.submod or "main"
            if package_name not in packages:
                raise ValueError(f"{source}: unknown submod {package_name}")
            relative_source = source.relative_to(ROOT_DIR)
            published_name = metadata.file_name or source.name
            relative_destination = relative_source.with_name(published_name)
            add_item(
                items,
                destinations,
                source=source,
                target=packages[package_name]["target_path"],
                relative_destination=relative_destination,
                package=package_name,
            )

    for package_name, package in packages.items():
        for source_name, destination_name in (package.get("root_files") or {}).items():
            source = (ROOT_DIR / source_name).resolve()
            if not source.is_file():
                raise FileNotFoundError(f"root publish file does not exist: {source}")
            relative_destination = Path(destination_name)
            if relative_destination.is_absolute() or ".." in relative_destination.parts:
                raise ValueError(
                    f"invalid root file destination for {package_name}: "
                    f"{relative_destination}"
                )
            add_item(
                items,
                destinations,
                source=source,
                target=package["target_path"],
                relative_destination=relative_destination,
                package=package_name,
            )

    return items


def clear_target(target: Path, *, dry_run: bool) -> int:
    if not target.exists():
        return 0
    if not target.is_dir():
        raise ValueError(f"publish target is not a directory: {target}")
    deleted_files = sum(1 for path in target.rglob("*") if path.is_file())
    print(f"DELETE {target}")
    if not dry_run:
        shutil.rmtree(target)
    return deleted_files


def publish(
    config_path: Path,
    *,
    dry_run: bool,
    selected_packages: set[str] | None = None,
) -> dict[str, dict[str, int]]:
    config = load_config(config_path)
    packages = package_configs(config, base=config_path.parent)
    unknown = (selected_packages or set()) - set(packages)
    if unknown:
        raise ValueError(f"unknown package(s): {', '.join(sorted(unknown))}")

    items = collect_publish_items(config, packages)
    if selected_packages:
        items = [item for item in items if item.package in selected_packages]
        packages = {
            name: package
            for name, package in packages.items()
            if name in selected_packages
        }

    result: dict[str, dict[str, int]] = {}

    for package_name, package in packages.items():
        target = package["target_path"]
        package_items = [item for item in items if item.package == package_name]
        deleted = clear_target(target, dry_run=dry_run)

        copied = 0
        for item in package_items:
            print(f"COPY   {item.source} -> {item.destination}")
            if not dry_run:
                item.destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item.source, item.destination)
            copied += 1

        result[package_name] = {
            "copied": copied,
            "deleted": deleted,
        }
        print(
            f"{package_name}: {copied} copied, {deleted} old files deleted "
            f"-> {target}"
        )

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Publish generated Stellaris runtime files to main and submod targets."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Publish config path (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--package",
        action="append",
        dest="packages",
        help="Publish only the named package; may be repeated.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print target deletion and copy operations without changing targets.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        publish(
            args.config.resolve(),
            dry_run=args.dry_run,
            selected_packages=set(args.packages) if args.packages else None,
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
