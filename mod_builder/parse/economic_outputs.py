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
    load_yaml,
    node_to_string,
)
from synthetipy.ast_nodes import BlockNode, PropertyNode

# ---- resource classification ----

ECONOMIC_RESOURCES = {
    'energy', 'minerals', 'food', 'alloys', 'consumer_goods',
    'physics_research', 'society_research', 'engineering_research',
    'trade', 'unity',
    'rare_crystals', 'volatile_motes', 'exotic_gases',
}

# ---- output data-class ----

@dataclass(frozen=True)
class EconomicProfiles:
    job_resource_outputs: dict[str, list[str]]
    job_resource_conditions: dict[str, dict[str, list[str | None]]]
    zone_resource_outputs: dict[str, list[str]]
    zone_resource_conditions: dict[str, dict[str, list[str | None]]]
    district_resource_profiles: dict[str, dict[str, object]]
    economic_district_slot_zone_outputs: dict[str, dict[str, list[str]]]
    economic_district_slot_zone_output_conditions: dict[str, dict[str, dict[str, list[str | None]]]]
    economic_district_slot_direct_outputs: dict[str, dict[str, list[str]]]
    economic_district_slot_direct_output_conditions: dict[str, dict[str, dict[str, list[str | None]]]]

# ---- helpers ----

def _ordered_unique(values: list[str]) -> list[str]:
    return list(OrderedDict.fromkeys(values))


def _ordered_unique_optional(values: list[str | None]) -> list[str | None]:
    unique = OrderedDict()
    for value in values:
        key = _condition_key(value)
        unique.setdefault(key, value)
    return list(unique.values())


def _condition_key(value):
    if isinstance(value, dict):
        return tuple((key, _condition_key(item)) for key, item in sorted(value.items()))
    if isinstance(value, list):
        return tuple(_condition_key(item) for item in value)
    return value


def _combine_conditions(*conditions):
    parts = []
    for condition in conditions:
        if condition is None:
            continue
        if isinstance(condition, dict) and "all" in condition:
            parts.extend(condition["all"])
        else:
            parts.append(condition)
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return {"all": parts}


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


def _filter_unconditional_outputs(
    outputs: list[str],
    resource_conditions: dict[str, list[str | None]],
) -> list[str]:
    return [
        output
        for output in outputs
        if output not in resource_conditions
        or None in resource_conditions.get(output, [])
    ]


def _filter_unconditional_resource_conditions(
    resource_conditions: dict[str, list[str | None]],
) -> dict[str, list[str | None]]:
    return {
        resource: [None]
        for resource, conditions in resource_conditions.items()
        if None in conditions
    }


def _build_slot_zone_outputs(
    districts: list[str],
    district_resource_profiles: dict[str, dict[str, object]],
) -> dict[str, list[str]]:
    zone_outputs: dict[str, list[str]] = {}

    for district in districts:
        profile = district_resource_profiles.get(district, {})
        zone_map = profile.get("zone_outputs", {})
        zone_conditions = profile.get("zone_output_conditions", {})

        for zone in profile.get("zones", zone_map.keys()):
            outputs = zone_map.get(zone, [])
            unconditional_outputs = _filter_unconditional_outputs(
                outputs,
                zone_conditions.get(zone, {}),
            )
            zone_outputs.setdefault(zone, [])
            zone_outputs[zone].extend(unconditional_outputs)

    return {
        zone: _ordered_unique(outputs)
        for zone, outputs in sorted(zone_outputs.items())
    }


def _merge_resource_conditions(
    target: dict[str, list[str | None]],
    source: dict[str, list[str | None]],
) -> None:
    for resource, conditions in source.items():
        target.setdefault(resource, [])
        target[resource].extend(conditions)


def _build_slot_direct_outputs(
    districts: list[str],
    district_resource_profiles: dict[str, dict[str, object]],
) -> dict[str, list[str]]:
    direct_outputs: dict[str, list[str]] = {}

    for district in districts:
        profile = district_resource_profiles.get(district, {})
        outputs = profile.get("controlled_direct_outputs", [])
        if not outputs:
            continue
        direct_outputs[district] = _ordered_unique(outputs)

    return {
        district: _ordered_unique(outputs)
        for district, outputs in sorted(direct_outputs.items())
        if outputs
    }


def _build_slot_direct_output_conditions(
    districts: list[str],
    district_resource_profiles: dict[str, dict[str, object]],
) -> dict[str, dict[str, list[str | None]]]:
    direct_conditions: dict[str, dict[str, list[str | None]]] = {}

    for district in districts:
        profile = district_resource_profiles.get(district, {})
        outputs = profile.get("controlled_direct_outputs", [])
        conditions = profile.get("controlled_direct_output_conditions", {})
        if not outputs:
            continue
        direct_conditions[district] = {
            resource: _ordered_unique_optional(conditions.get(resource, [None]))
            for resource in outputs
        }

    return {
        district: {
            resource: condition_list
            for resource, condition_list in sorted(resource_conditions.items())
            if condition_list
        }
        for district, resource_conditions in sorted(direct_conditions.items())
        if resource_conditions
    }


def _build_slot_zone_output_conditions(
    districts: list[str],
    district_resource_profiles: dict[str, dict[str, object]],
) -> dict[str, dict[str, list[str | None]]]:
    zone_conditions: dict[str, dict[str, list[str | None]]] = {}

    for district in districts:
        profile = district_resource_profiles.get(district, {})
        zone_map = profile.get("zone_output_conditions", {})

        for zone, resource_conditions in zone_map.items():
            unconditional_conditions = _filter_unconditional_resource_conditions(
                resource_conditions,
            )
            if not unconditional_conditions:
                continue
            zone_conditions.setdefault(zone, {})
            _merge_resource_conditions(zone_conditions[zone], unconditional_conditions)

    return {
        zone: {
            resource: _ordered_unique_optional(conditions)
            for resource, conditions in sorted(resource_conditions.items())
            if conditions
        }
        for zone, resource_conditions in sorted(zone_conditions.items())
        if resource_conditions
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


def _extract_job_entries(node, valid_jobs: set[str]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for prop in iter_property_nodes(node):
        key = str(prop.key)
        if not key.startswith("job_") or not key.endswith("_add"):
            continue
        job_key = key[len("job_") : -len("_add")]
        if job_key not in valid_jobs:
            continue
        entries.append({
            "job": job_key,
            "condition": _job_add_wrapper_condition(prop),
        })
    return entries


def _job_add_wrapper_condition(job_prop: PropertyNode):
    conditions: list[str] = []
    current = job_prop.parent

    while current is not None:
        if isinstance(current, BlockNode):
            potential = current.get_property("potential")
            if potential is not None:
                condition = node_to_string(potential.value)
                if condition:
                    conditions.append(condition)
        current = getattr(current, "parent", None)

    return _combine_conditions(*conditions)


def _job_resource_outputs_from_produces(context: ParseContext) -> dict[str, list[str]]:
    job_resources = _parse_job_resources(context)
    job_outputs: dict[str, list[str]] = {}
    for job_name, resource_info in job_resources.items():
        outputs: list[str] = []
        for entry in resource_info.get("produces", []):
            outputs.extend(
                resource
                for resource in entry.get("resources", {})
                if resource in ECONOMIC_RESOURCES
            )
        if outputs:
            job_outputs[job_name] = _ordered_unique(outputs)
    return job_outputs


def _job_resource_conditions_from_produces(
    context: ParseContext,
) -> dict[str, dict[str, list[str | None]]]:
    job_resources = _parse_job_resources(context)
    job_conditions: dict[str, dict[str, list[str | None]]] = {}
    for job_name, resource_info in job_resources.items():
        resource_conditions: dict[str, list[str | None]] = {}
        for entry in resource_info.get("produces", []):
            trigger = entry.get("trigger")
            for resource in entry.get("resources", {}):
                if resource not in ECONOMIC_RESOURCES:
                    continue
                resource_conditions.setdefault(resource, []).append(trigger)
        if resource_conditions:
            job_conditions[job_name] = {
                resource: _ordered_unique_optional(conditions)
                for resource, conditions in resource_conditions.items()
            }
    return job_conditions


def _extract_resource_outputs_from_jobs(
    node,
    valid_jobs: set[str],
    job_resource_outputs: dict[str, list[str]],
) -> list[str]:
    outputs: list[str] = []
    for job_key in _extract_job_keys(node, valid_jobs):
        outputs.extend(job_resource_outputs.get(job_key, []))
    return _ordered_unique(outputs)


def _extract_resource_conditions_from_jobs(
    node,
    valid_jobs: set[str],
    job_resource_conditions: dict[str, dict[str, list[str | None]]],
    include_wrapper_conditions: bool = False,
) -> dict[str, list[str | None]]:
    resource_conditions: dict[str, list[str | None]] = {}
    if not include_wrapper_conditions:
        for job_key in _extract_job_keys(node, valid_jobs):
            _merge_resource_conditions(
                resource_conditions,
                job_resource_conditions.get(job_key, {}),
            )
        return {
            resource: _ordered_unique_optional(conditions)
            for resource, conditions in resource_conditions.items()
            if conditions
        }

    for entry in _extract_job_entries(node, valid_jobs):
        job_key = entry["job"]
        wrapper_condition = entry["condition"]
        for resource, conditions in job_resource_conditions.get(job_key, {}).items():
            resource_conditions.setdefault(resource, [])
            resource_conditions[resource].extend(
                _combine_conditions(wrapper_condition, condition)
                for condition in conditions
            )
    return {
        resource: _ordered_unique_optional(conditions)
        for resource, conditions in resource_conditions.items()
        if conditions
    }

# ---- existing economic profile builders ----

def build_economic_profiles(
    context: ParseContext,
    graph: ZoneParseGraph | None = None,
) -> EconomicProfiles:
    graph = graph or build_zone_parse_graph(context)
    job_resource_outputs = _job_resource_outputs_from_produces(context)
    job_resource_conditions = _job_resource_conditions_from_produces(context)
    valid_jobs = set(context.ast["common/pop_jobs"].keys())
    district_direct_outputs_config = context.load_config("district_direct_outputs.yaml").get(
        "district_direct_outputs",
        {},
    )

    zone_resource_outputs: dict[str, list[str]] = {}
    zone_resource_conditions: dict[str, dict[str, list[str | None]]] = {}
    for zone_name, zone in context.ast["common/zones"].items():
        outputs = _extract_resource_outputs_from_jobs(zone.body, valid_jobs, job_resource_outputs)
        if outputs:
            zone_resource_outputs[zone_name] = outputs
            zone_resource_conditions[zone_name] = _extract_resource_conditions_from_jobs(
                zone.body,
                valid_jobs,
                job_resource_conditions,
            )

    district_resource_profiles: dict[str, dict[str, object]] = {}
    for district_name, district in context.ast["common/districts"].items():
        parsed_direct_outputs = _extract_resource_outputs_from_jobs(
            district.body,
            valid_jobs,
            job_resource_outputs,
        )
        direct_outputs = _ordered_unique(
            district_direct_outputs_config.get(district_name, parsed_direct_outputs)
        )
        controlled_direct_outputs = _ordered_unique(
            district_direct_outputs_config.get(district_name, [])
        )
        parsed_direct_conditions = _extract_resource_conditions_from_jobs(
            district.body,
            valid_jobs,
            job_resource_conditions,
            include_wrapper_conditions=True,
        )
        direct_output_conditions = (
            {resource: [None] for resource in direct_outputs}
            if district_name in district_direct_outputs_config
            else parsed_direct_conditions
        )

        district_zones = graph.district_to_zones.get(district_name, [])
        zone_outputs: dict[str, list[str]] = {}
        zone_output_conditions: dict[str, dict[str, list[str | None]]] = {}
        for zone_name in district_zones:
            outputs = zone_resource_outputs.get(zone_name, [])
            if outputs:
                zone_outputs[zone_name] = outputs
                zone_output_conditions[zone_name] = zone_resource_conditions.get(zone_name, {})

        district_resource_profiles[district_name] = {
            "zones": district_zones,
            "direct_outputs": direct_outputs,
            "direct_output_conditions": direct_output_conditions,
            "controlled_direct_outputs": controlled_direct_outputs,
            "controlled_direct_output_conditions": {
                resource: [None]
                for resource in controlled_direct_outputs
            },
            "zone_outputs": zone_outputs,
            "zone_output_conditions": zone_output_conditions,
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
    economic_district_slot_zone_output_conditions: dict[str, dict[str, dict[str, list[str | None]]]] = {}
    economic_district_slot_direct_outputs: dict[str, dict[str, list[str]]] = {}
    economic_district_slot_direct_output_conditions: dict[str, dict[str, dict[str, list[str | None]]]] = {}
    for slot, districts in slot_districts.items():
        economic_district_slot_zone_outputs[slot] = _build_slot_zone_outputs(
            districts,
            district_resource_profiles,
        )
        economic_district_slot_zone_output_conditions[slot] = _build_slot_zone_output_conditions(
            districts,
            district_resource_profiles,
        )
        economic_district_slot_direct_outputs[slot] = _build_slot_direct_outputs(
            districts,
            district_resource_profiles,
        )
        economic_district_slot_direct_output_conditions[slot] = _build_slot_direct_output_conditions(
            districts,
            district_resource_profiles,
        )

    return EconomicProfiles(
        job_resource_outputs=job_resource_outputs,
        job_resource_conditions=job_resource_conditions,
        zone_resource_outputs=zone_resource_outputs,
        zone_resource_conditions=zone_resource_conditions,
        district_resource_profiles=district_resource_profiles,
        economic_district_slot_zone_outputs=economic_district_slot_zone_outputs,
        economic_district_slot_zone_output_conditions=economic_district_slot_zone_output_conditions,
        economic_district_slot_direct_outputs=economic_district_slot_direct_outputs,
        economic_district_slot_direct_output_conditions=economic_district_slot_direct_output_conditions,
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
        "job_resource_conditions.yaml",
        {"job_resource_conditions": profiles.job_resource_conditions},
    )
    context.write_generated_yaml(
        "zone_resource_outputs.yaml",
        {"zone_resource_outputs": profiles.zone_resource_outputs},
    )
    context.write_generated_yaml(
        "zone_resource_conditions.yaml",
        {"zone_resource_conditions": profiles.zone_resource_conditions},
    )
    context.write_generated_yaml(
        "district_resource_profiles.yaml",
        {"district_resource_profiles": profiles.district_resource_profiles},
    )
    context.write_generated_yaml(
        "economic_district_slot_groups.yaml",
        {"economic_district_slot_zone_outputs": profiles.economic_district_slot_zone_outputs},
    )
    context.write_generated_yaml(
        "economic_district_slot_conditions.yaml",
        {
            "economic_district_slot_zone_output_conditions": (
                profiles.economic_district_slot_zone_output_conditions
            ),
            "economic_district_slot_direct_output_conditions": (
                profiles.economic_district_slot_direct_output_conditions
            ),
        },
    )
    context.write_generated_yaml(
        "economic_district_slot_direct_groups.yaml",
        {"economic_district_slot_direct_outputs": profiles.economic_district_slot_direct_outputs},
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


def _normalize_job_icon(job_name: str, icon_name: str | None) -> str:
    """返回 gfx/interface/icons/jobs/<icon>.dds 使用的 basename。"""
    icon = (icon_name or "").strip().strip('"')
    if not icon:
        icon = job_name
    if not icon.startswith("job_"):
        icon = f"job_{icon}"
    return icon


def _extract_job_icons(context: ParseContext) -> dict[str, str]:
    """从 pop_jobs/ 中提取岗位图标 basename。

    默认图标是 job_<job>.dds；swappable_data.default.icon 会覆写为 job_<icon>.dds。
    """
    icons: dict[str, str] = {}
    for job_name, job_node in context.ast["common/pop_jobs"].items():
        override_icon: str | None = None
        swappable_prop = job_node.body.get_property("swappable_data")
        if swappable_prop is not None and isinstance(swappable_prop.value, BlockNode):
            default_prop = swappable_prop.value.get_property("default")
            if default_prop is not None and isinstance(default_prop.value, BlockNode):
                icon_prop = default_prop.value.get_property("icon")
                if icon_prop is not None:
                    override_icon = str(icon_prop.value)

        icons[job_name] = _normalize_job_icon(job_name, override_icon)
    return icons


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


def _resolve_economic_category_parents(
    category_name: str | None,
    cat_data: dict[str, dict],
) -> list[str]:
    """Return the parent chain for an economic category, nearest parent first."""
    if not category_name:
        return []

    parents: list[str] = []
    visited: set[str] = set()
    current = category_name
    while current and current not in visited:
        visited.add(current)
        info = cat_data.get(current)
        if not info:
            break
        parent = info.get("parent")
        if not parent:
            break
        parents.append(parent)
        current = parent
    return parents


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
    job_icons: dict[str, str],
    job_resources: dict[str, dict],
    economic_category_data: dict[str, dict],
) -> dict[str, dict]:
    """综合 pop_category + icon + resources 数据，构建统一的 job_meta。"""
    job_meta: dict[str, dict] = {}

    for job_name, res_info in job_resources.items():
        pop_category = pop_categories.get(job_name)
        economic_category = res_info.get("economic_category")
        icon = job_icons.get(job_name, _normalize_job_icon(job_name, None))

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
            "economic_category_parents": _resolve_economic_category_parents(
                economic_category,
                economic_category_data,
            ),
            "icon": icon,
            "produces": produces_flat,
            "is_economic_producer": is_economic_producer,
            "economic_resources": economic_resources,
        }

    return job_meta


def render_job_meta(context: ParseContext) -> dict[str, dict]:
    """生成 job_meta.yaml 的入口函数。"""
    pop_categories = _extract_job_pop_categories(context)
    job_icons = _extract_job_icons(context)
    job_resources = _parse_job_resources(context)
    economic_category_data = _extract_economic_category_icons(context)
    job_meta = _build_job_meta(
        pop_categories,
        job_icons,
        job_resources,
        economic_category_data,
    )

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
