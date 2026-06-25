"""岗位调控编译器：从手写配置 + job_meta 推导出模板可用的调控配置文件。"""

from __future__ import annotations

from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from framework import load_yaml


GENERATED_CONFIG_DIR = (
    Path(__file__).resolve().parents[1] / "templates" / "generated_configs"
)
CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs"


def compile_job_regulation(generated_configs_dir: Path | None = None) -> dict:
    """编译岗位调控配置，返回结果 dict 并写入 YAML。"""
    if generated_configs_dir is None:
        generated_configs_dir = GENERATED_CONFIG_DIR

    # 加载手写配置
    regulation = load_yaml(CONFIGS_DIR / "job_regulation.yaml").get("job_regulation", {})
    gear_steps = regulation.get("gear_steps", [3200, 800, 200, 50])
    blacklist = set(regulation.get("blacklist_jobs", []))

    # 加载解析生成的 job_meta
    job_meta = load_yaml(generated_configs_dir / "job_meta.yaml").get("job_meta", {})

    # 资源 → needs_category 映射
    RESOURCE_NEEDS_MAP = {
        "energy": "energy",
        "minerals": "minerals",
        "food": "food",
        "alloys": "alloys",
        "consumer_goods": "consumer_goods",
        "physics_research": "physics_research",
        "society_research": "society_research",
        "engineering_research": "engineering_research",
    }

    # 筛选经济岗位
    regulated_jobs: list[dict] = []
    for job_name, meta in sorted(job_meta.items()):
        if not meta.get("is_economic_producer"):
            continue
        if job_name in blacklist:
            continue

        economic_resources = meta.get("economic_resources", [])
        # 去重 needs_category
        needs_cats = list(dict.fromkeys(
            RESOURCE_NEEDS_MAP.get(r, r) for r in economic_resources
        ))

        entry = {
            "job": job_name,
            "pop_category": meta.get("pop_category"),
            "icon": meta.get("icon"),
            "economic_category": meta.get("economic_category"),
            "economic_resources": economic_resources,
            "needs_categories": needs_cats,
            "primary_needs": needs_cats[0] if needs_cats else None,
            "produces": meta.get("produces", []),
        }
        regulated_jobs.append(entry)

    config = {
        "gear_steps": gear_steps,
        "display_slots": regulation.get("display_slots", 15),
        "regulated_jobs": regulated_jobs,
    }

    # 写入 YAML
    from framework import write_yaml
    write_yaml(
        generated_configs_dir / "job_regulation_config.yaml",
        {"job_regulation_config": config},
    )

    print(f"Compiled job_regulation_config: {len(regulated_jobs)} regulated jobs, "
          f"gear_steps={gear_steps}")

    return config


def main() -> None:
    compile_job_regulation()


if __name__ == "__main__":
    main()
