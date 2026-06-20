import shutil
from pathlib import Path

from building_strategy_compile import compile_building_strategies


def copy_configs():
    # Setup paths
    base_dir = Path(__file__).parent.parent
    configs_dir = base_dir / "configs"
    generated_configs_dir = base_dir / "templates" / "generated_configs"

    # Ensure output directory exists
    generated_configs_dir.mkdir(parents=True, exist_ok=True)

    # List of files to copy
    files_to_copy = [
        "job_config.yaml",
        "other_district_config.yaml",
        "all_designations.yaml",
    ]

    for filename in files_to_copy:
        src = configs_dir / filename
        dst = generated_configs_dir / filename
        if src.exists():
            shutil.copy2(src, dst)
            print(f"Copied {filename} to generated_configs")
        else:
            print(f"Warning: Source file {src} does not exist.")

    compile_building_strategies(
        configs_dir / "buildings",
        generated_configs_dir,
    )
    print("Compiled building strategy configs to generated_configs")


if __name__ == "__main__":
    copy_configs()
