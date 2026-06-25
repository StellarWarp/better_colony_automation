from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from framework import (
    ParseContext,
    ZoneParseGraph,
    build_zone_parse_graph,
    iter_property_nodes,
    list_node_values,
    load_yaml,
    node_to_string,
)
from synthetipy.ast_nodes import BlockNode, ListNode, PropertyNode

# ---- resource classification ----

ECONOMIC_RESOURCES = {
    'energy', 'minerals', 'food', 'alloys', 'consumer_goods',
    'physics_research', 'society_research', 'engineering_research',
}

# ---- output data-class ----

@dataclass(frozen=True)
class EconomicProfiles:
    job_resource_outputs: dict[str, list[str]]
    zone_resource_outputs: dict[str, list[str]]
    district_resource_profiles: dict[str, dict[str, object]]
    economic_district_slot_zone_outputs: dict[str, dict[str, list[str]]]

# ---- helpers ----

def _ordered_unique(values: list[str]) -> list[str]:
    return list(OrderedDict.fromkeys(values))


def _invert_zone_outputs(
    zone_outputs: dict[str, list[str]],
    excluded_outputs: list[str] | None = None,
) -> dict[str, list[str]]:
    excluded = set(excluded_outputs or [])
    output_zones: dict[str, list[str]] = {}
    for zone, outputs in zone_outputs.items():
        for output in outputs:
            if output in excluded:
                continue
            output_zones.setdefault(output, []).append(zone)
    return {
        output: _ordered_unique(zones)
        for output, zones in output_zones.items()
    }


def _build_slot_zone_outputs(
    districts: list[str],
    district_resource_profiles: dict[str, dict[str, object]],
) -> dict[str, list[str]]:
    zone_outputs: dict[str, list[str]] = {}

    for district in districts:
        profile = district_resource_profiles.get(district, {})
        direct_outputs = profile.get("direct_outputs", [])
        zone_map = profile.get("zone_outputs", {})

        for zone, outputs in zone_map.items():
            zone_outputs.setdefault(zone, [])
            zone_outputs[zone].extend(direct_outputs)
            zone_outputs[zone].extend(outputs)

    return {
        zone: _ordered_unique(outputs)
        for zone, outputs in sorted(zone_outputs.items())
        if outputs
    }


def _extract_job_keys(node, valid_jobs: set[str]) -> list[str]:
    jobs: list[str] = []
    for prop in iter_property_nodes(node):
        key = str(prop.key)
        if not key.startswith("job_") or not key.endswith("_add"):
            continue
        job_key = key[len("job_") : -len("_add")]
        if job_key in valid_jobs:
            jobs.append(job_key)
    return _ordered_unique(jobs)


def _job_tag_outputs(context: ParseContext) -> dict[str, list[str]]:
    tag_output_mapping = context.load_config("job_tag_outputs.yaml").get("job_tag_outputs", {})
    job_outputs: dict[str, list[str]] = {}

    for name, job in context.ast["common/pop_jobs"].items():
        tags: list[str] = []
        for stat in job.body.statements:
            if not isinstance(stat, PropertyNode) or str(stat.key) != "tags":
                continue
            if isinstance(stat.value, ListNode):
                tags.extend(list_node_values(stat.value, "tags", name))
        outputs: list[str] = []
        for tag in tags:
            outputs.extend(tag_output_mapping.get(tag, []))
        if outputs:
            job_outputs[name] = _ordered_unique(outputs)

    return job_outputs

# ---- existing economic profile builders ----

def build_economic_profiles(
    context: ParseContext,
    graph: ZoneParseGraph | None = None,
) -> EconomicProfiles:
    graph = graph or build_zone_parse_graph(context)
    job_resource_outputs = _job_tag_outputs(context)
    valid_jobs = set(context.ast["common/pop_jobs"].keys())
    district_direct_outputs_config = context.load_config("district_direct_outputs.yaml").get(
        "district_direct_outputs",
        {},
    )

    zone_resource_outputs: dict[str, list[str]] = {}
    for zone_name, zone in context.ast["common/zones"].items():
        outputs: list[str] = []
        for job_key in _extract_job_keys(zone.body, valid_jobs):
            outputs.extend(job_resource_outputs.get(job_key, []))
        if outputs:
            zone_resource_outputs[zone_name] = _ordered_unique(outputs)

    district_resource_profiles: dict[str, dict[str, object]] = {}
    for district_name, district in context.ast["common/districts"].items():
        direct_outputs = _ordered_unique(district_direct_outputs_config.get(district_name, []))

        zone_outputs: dict[str, list[str]] = {}
        for zone_name in graph.district_to_zones.get(district_name, []):
            outputs = zone_resource_outputs.get(zone_name, [])
            if outputs:
                zone_outputs[zone_name] = outputs

        district_resource_profiles[district_name] = {
            "direct_outputs": direct_outputs,
            "zone_outputs": zone_outputs,
            "output_zones": _invert_zone_outputs(zone_outputs, direct_outputs),
        }

    other_district_config = context.load_config("other_district_config.yaml")
    used_districts = load_yaml(context.generated_configs_dir / "used_districts.yaml")
    slot_districts = {
        "d0": used_districts.get("primary_districts", []),
        "d1": other_district_config.get("secondary_districts_d1", []),
        "d2": other_district_config.get("secondary_districts_d2", []),
        "d3": other_district_config.get("secondary_districts_d3", []),
    }
    economic_district_slot_zone_outputs: dict[str, dict[str, list[str]]] = {}
    for slot, districts in slot_districts.items():
        economic_district_slot_zone_outputs[slot] = _build_slot_zone_outputs(
            districts,
            district_resource_profiles,
        )

    return EconomicProfiles(
        job_resource_outputs=job_resource_outputs,
        zone_resource_outputs=zone_resource_outputs,
        district_resource_profiles=district_resource_profiles,
        economic_district_slot_zone_outputs=economic_district_slot_zone_outputs,
    )


def render_economic_generated_configs(
    context: ParseContext,
    graph: ZoneParseGraph | None = None,
) -> EconomicProfiles:
    profiles = build_economic_profiles(context, graph)
    context.write_generated_yaml(
        "job_resource_outputs.yaml",
        {"job_resource_outputs": profiles.job_resource_outputs},
    )
    context.write_generated_yaml(
        "zone_resource_outputs.yaml",
        {"zone_resource_outputs": profiles.zone_resource_outputs},
    )
    context.write_generated_yaml(
        "district_resource_profiles.yaml",
        {"district_resource_profiles": profiles.district_resource_profiles},
    )
    context.write_generated_yaml(
        "economic_district_slot_groups.yaml",
        {"economic_district_slot_zone_outputs": profiles.economic_district_slot_zone_outputs},
    )
    return profiles


# ============================================================
#  Phase 1: 完整岗位经济数据解析
# ============================================================

def _extract_job_pop_categories(context: ParseContext) -> dict[str, str]:
    """从 pop_jobs/ 中提取每个岗位的 pop_category（阶级）。"""
    categories: dict[str, str] = {}
    for job_name, job_node in context.ast["common/pop_jobs"].items():
        pop_cat = job_node.body.get_property("category")
        if pop_cat is not None:
            categories[job_name] = str(pop_cat.value)
    return categories


def _extract_economic_category_icons(context: ParseContext) -> dict[str, dict]:
    """从 economic_categories/ 中提取 icon 和 parent 链。

    返回: {category_name: {icon: str, parent: str|None}}
    """
    result: dict[str, dict] = {}
    for cat_name, cat_node in context.ast["common/economic_categories"].items():
        entry: dict = {"icon": None, "parent": None}
        icon_prop = cat_node.body.get_property("icon")
        if icon_prop is not None:
            entry["icon"] = str(icon_prop.value).strip('"')
        parent_prop = cat_node.body.get_property("parent")
        if parent_prop is not None:
            entry["parent"] = str(parent_prop.value)
        result[cat_name] = entry
    return result


def _resolve_economic_category_icon(
    category_name: str,
    cat_data: dict[str, dict],
    _visited: set | None = None,
) -> str | None:
    """沿 parent 链解析 icon，处理 use_parent_icon 和继承。"""
    if _visited is None:
        _visited = set()
    if category_name in _visited:
        return None  # 循环引用
    _visited.add(category_name)

    info = cat_data.get(category_name)
    if info is None:
        return None
    if info["icon"]:
        return info["icon"]
    if info["parent"]:
        return _resolve_economic_category_icon(info["parent"], cat_data, _visited)
    return None


def _parse_job_resources(context: ParseContext) -> dict[str, dict]:
    """解析每个岗位的 resources 块（category + produces 列表）。"""
    result: dict[str, dict] = {}
    ast_jobs = context.ast["common/pop_jobs"]

    for job_name, job_node in ast_jobs.items():
        resources_node = job_node.body.get_property("resources")
        if resources_node is None or not isinstance(resources_node.value, BlockNode):
            result[job_name] = {"economic_category": None, "produces": []}
            continue

        resources_block = resources_node.value

        # --- resources.category ---
        eco_cat_prop = resources_block.get_property("category")
        economic_category = str(eco_cat_prop.value) if eco_cat_prop is not None else None

        # --- resources.produces ---
        produces_entries: list[dict] = []
        for stmt in resources_block.statements:
            if not isinstance(stmt, PropertyNode):
                continue
            if str(stmt.key) != "produces":
                continue
            if not isinstance(stmt.value, BlockNode):
                continue

            produces_block = stmt.value
            trigger_text: str | None = None
            resources: dict[str, float] = {}

            for prod_stmt in produces_block.statements:
                if not isinstance(prod_stmt, PropertyNode):
                    continue
                key = str(prod_stmt.key)

                if key == "trigger":
                    # 提取 trigger 文本（内部语句，不含外层 trigger = { } 包装）
                    if isinstance(prod_stmt.value, BlockNode):
                        trigger_parts = []
                        for t_stmt in prod_stmt.value.statements:
                            trigger_parts.append(node_to_string(t_stmt))
                        trigger_text = "\n            ".join(trigger_parts)
                    continue

                # 普通资源条目: resource_name = amount
                try:
                    amount = float(str(prod_stmt.value))
                except (ValueError, TypeError):
                    continue
                resources[key] = amount

            produces_entries.append({
                "trigger": trigger_text,
                "resources": resources,
            })

        result[job_name] = {
            "economic_category": economic_category,
            "produces": produces_entries,
        }

    return result


def _build_job_meta(
    pop_categories: dict[str, str],
    eco_cat_data: dict[str, dict],
    job_resources: dict[str, dict],
) -> dict[str, dict]:
    """综合 pop_category + icon + resources 数据，构建统一的 job_meta。"""
    job_meta: dict[str, dict] = {}

    for job_name, res_info in job_resources.items():
        pop_category = pop_categories.get(job_name)
        economic_category = res_info.get("economic_category")

        # 解析 icon
        icon: str | None = None
        if economic_category:
            icon = _resolve_economic_category_icon(economic_category, eco_cat_data)

        # 从 produces 条目中提取资源产出列表
        all_resource_outputs: list[str] = []
        produces_flat: list[dict] = []

        for entry in res_info.get("produces", []):
            for resource, amount in entry["resources"].items():
                all_resource_outputs.append(resource)
                produces_flat.append({
                    "resource": resource,
                    "amount": amount,
                    "trigger": entry["trigger"],
                })

        economic_resources = [
            r for r in _ordered_unique(all_resource_outputs)
            if r in ECONOMIC_RESOURCES
        ]
        is_economic_producer = len(economic_resources) > 0

        job_meta[job_name] = {
            "pop_category": pop_category,
            "economic_category": economic_category,
            "icon": icon,
            "produces": produces_flat,
            "is_economic_producer": is_economic_producer,
            "economic_resources": economic_resources,
        }

    return job_meta


def render_job_meta(context: ParseContext) -> dict[str, dict]:
    """生成 job_meta.yaml 的入口函数。"""
    pop_categories = _extract_job_pop_categories(context)
    eco_cat_data = _extract_economic_category_icons(context)
    job_resources = _parse_job_resources(context)
    job_meta = _build_job_meta(pop_categories, eco_cat_data, job_resources)

    context.write_generated_yaml("job_meta.yaml", {"job_meta": job_meta})

    # 统计
    economic_count = sum(1 for v in job_meta.values() if v["is_economic_producer"])
    total_count = len(job_meta)
    print(f"Generated job_meta.yaml: {total_count} jobs, "
          f"{economic_count} economic producers")

    return job_meta


# ---- entry-points ----

def main() -> None:
    context = ParseContext.build()
    render_economic_generated_configs(context)


if __name__ == "__main__":
    main()
