"""岗位调控编译器：从手写配置 + job_meta 推导出模板可用的调控配置文件。"""

from __future__ import annotations

import re
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from framework import load_yaml


GENERATED_CONFIG_DIR = (
    Path(__file__).resolve().parents[1] / "templates" / "generated_configs"
)
CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs"
MODIFIER_DOC_PATH = (
    Path.home()
    / "Documents"
    / "Paradox Interactive"
    / "Stellaris"
    / "logs"
    / "script_documentation"
    / "modifiers.log"
)
MODIFIER_LINE_RE = re.compile(r"^-\s*([A-Za-z0-9_:.\-]+),\s*Category:")


def _load_known_modifiers(path: Path = MODIFIER_DOC_PATH) -> set[str]:
    if not path.exists():
        print(f"Warning: modifier documentation not found: {path}")
        return set()

    modifiers: set[str] = set()
    with path.open("r", encoding="utf-8-sig", errors="ignore") as f:
        for line in f:
            match = MODIFIER_LINE_RE.match(line.strip())
            if match:
                modifiers.add(match.group(1))
    print(f"Loaded modifier documentation: {len(modifiers)} modifiers")
    return modifiers


def _build_category_resource_add_modifiers(
    known_modifiers: set[str],
    resources: list[str],
) -> dict[str, dict[str, str]]:
    """Find <economic_category>_<resource>_produces_add modifiers for known resources."""
    by_category: dict[str, dict[str, str]] = {}
    resources_by_length = sorted(resources, key=len, reverse=True)

    for modifier in known_modifiers:
        for resource in resources_by_length:
            suffix = f"_{resource}_produces_add"
            if not modifier.endswith(suffix):
                continue
            category = modifier[: -len(suffix)]
            by_category.setdefault(category, {})[resource] = modifier
            break

    return by_category


def _modifier_positive_trigger(modifier: str) -> str:
    return (
        "check_modifier_value = {\n"
        f"    modifier = {modifier}\n"
        "    value > 0\n"
        "}"
    )


def _category_chain(meta: dict) -> list[str]:
    category = meta.get("economic_category")
    chain = [category] if category else []
    chain.extend(meta.get("economic_category_parents", []))
    return chain


def _apply_modifier_driven_extra_outputs(
    meta: dict,
    economic_resources: list[str],
    produces: list[dict],
    category_resource_add_modifiers: dict[str, dict[str, str]],
    resource_set: set[str],
) -> None:
    existing_resources = set(economic_resources)

    for category in _category_chain(meta):
        for resource, modifier in category_resource_add_modifiers.get(category, {}).items():
            if resource not in resource_set:
                continue
            if resource in existing_resources:
                continue
            economic_resources.append(resource)
            existing_resources.add(resource)
            produces.append({
                "resource": resource,
                "amount": 0,
                "trigger": _modifier_positive_trigger(modifier),
            })


def compile_job_regulation(generated_configs_dir: Path | None = None) -> dict:
    """编译岗位调控配置，返回结果 dict 并写入 YAML。"""
    if generated_configs_dir is None:
        generated_configs_dir = GENERATED_CONFIG_DIR

    # 加载手写配置
    regulation = load_yaml(CONFIGS_DIR / "job_regulation.yaml").get("job_regulation", {})
    economic_need_thresholds = load_yaml(CONFIGS_DIR / "economic_need_thresholds.yaml").get(
        "economic_need_thresholds", {}
    )
    gear_steps = regulation.get("gear_steps", [3200, 800, 200, 50])
    default_manual_manage_jobs = set(regulation.get("default_manual_manage_jobs", []))

    # 加载解析生成的 job_meta
    job_meta = load_yaml(generated_configs_dir / "job_meta.yaml").get("job_meta", {})

    # 资源顺序跟随经济阈值配置，模板和 GUI 统一消费这份列表。
    resources = list(economic_need_thresholds.keys())
    resource_set = set(resources)
    category_resource_add_modifiers = _build_category_resource_add_modifiers(
        _load_known_modifiers(),
        resources,
    )

    # 筛选经济岗位
    regulated_jobs: list[dict] = []
    icon_sprites: list[str] = []
    seen_icons: set[str] = set()
    regulated_job_names: set[str] = set()
    for job_name, meta in sorted(job_meta.items()):
        if not meta.get("is_economic_producer"):
            continue

        economic_resources = [r for r in meta.get("economic_resources", []) if r in resource_set]
        produces = [dict(prod) for prod in meta.get("produces", [])]
        _apply_modifier_driven_extra_outputs(
            meta,
            economic_resources,
            produces,
            category_resource_add_modifiers,
            resource_set,
        )
        # 去重 needs_category
        needs_cats = list(dict.fromkeys(economic_resources))
        icon = meta.get("icon")
        if icon and icon not in seen_icons:
            seen_icons.add(icon)
            icon_sprites.append(icon)

        entry = {
            "job": job_name,
            "pop_category": meta.get("pop_category"),
            "icon": icon,
            "economic_category": meta.get("economic_category"),
            "economic_category_parents": meta.get("economic_category_parents", []),
            "economic_resources": economic_resources,
            "needs_categories": needs_cats,
            "primary_needs": needs_cats[0] if needs_cats else None,
            "produces": produces,
        }
        regulated_jobs.append(entry)
        regulated_job_names.add(job_name)

    unknown_default_manual_jobs = sorted(default_manual_manage_jobs - regulated_job_names)
    if unknown_default_manual_jobs:
        print(
            "Warning: default_manual_manage_jobs contains jobs that are not "
            f"regulated economic jobs: {', '.join(unknown_default_manual_jobs)}"
        )

    config = {
        "gear_steps": gear_steps,
        "display_slots": regulation.get("display_slots", 15),
        "resources": resources,
        "categories": resources,
        "regulated_jobs": regulated_jobs,
        "default_manual_manage_jobs": sorted(default_manual_manage_jobs & regulated_job_names),
        "icon_sprites": icon_sprites,
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
