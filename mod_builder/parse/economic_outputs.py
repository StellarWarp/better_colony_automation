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
)
from synthetipy.ast_nodes import ListNode, PropertyNode


@dataclass(frozen=True)
class EconomicProfiles:
    job_resource_outputs: dict[str, list[str]]
    zone_resource_outputs: dict[str, list[str]]
    district_resource_profiles: dict[str, dict[str, object]]
    economic_district_slot_zone_outputs: dict[str, dict[str, list[str]]]


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


def main() -> None:
    context = ParseContext.build()
    render_economic_generated_configs(context)


if __name__ == "__main__":
    main()
