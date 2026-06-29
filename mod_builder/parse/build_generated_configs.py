from __future__ import annotations

import shutil
from pathlib import Path

from building_condition import render_building_conditions
from building_strategy_compile import compile_building_strategies
from economic_outputs import render_economic_generated_configs, render_job_meta
from job_regulation_compile import compile_job_regulation
from framework import ParseContext, load_yaml, write_yaml
from zone_outputs import render_zone_generated_configs


def copy_handwritten_configs(base_dir: Path, generated_configs_dir: Path) -> None:
    configs_dir = base_dir / "configs"
    generated_configs_dir.mkdir(parents=True, exist_ok=True)

    files_to_copy = [
        "district_direct_outputs.yaml",
        "other_district_config.yaml",
        "all_designations.yaml",
        "economic_need_thresholds.yaml",
    ]

    for filename in files_to_copy:
        src = configs_dir / filename
        dst = generated_configs_dir / filename
        if src.exists():
            shutil.copy2(src, dst)
            print(f"Copied {filename} to generated_configs")
        else:
            print(f"Warning: Source file {src} does not exist.")

    zone_type_resources_src = configs_dir / "zone_type_resources.yaml"
    zone_type_resources_dst = generated_configs_dir / "zone_type_resources.yaml"
    if zone_type_resources_src.exists():
        write_yaml(
            zone_type_resources_dst,
            {"zone_type_resources": load_yaml(zone_type_resources_src)},
        )
        print("Copied zone_type_resources.yaml to generated_configs")
    else:
        print(f"Warning: Source file {zone_type_resources_src} does not exist.")


def build_generated_configs() -> None:
    base_dir = Path(__file__).parent.parent
    generated_configs_dir = base_dir / "templates" / "generated_configs"

    copy_handwritten_configs(base_dir, generated_configs_dir)

    context = ParseContext.build()
    graph = render_zone_generated_configs(context)
    render_economic_generated_configs(context, graph)
    render_job_meta(context)
    render_building_conditions()

    compile_job_regulation(generated_configs_dir)
    print("Compiled job regulation config to generated_configs")

    compile_building_strategies(
        base_dir / "configs" / "buildings",
        generated_configs_dir,
    )
    print("Compiled building strategy configs to generated_configs")


if __name__ == "__main__":
    build_generated_configs()
