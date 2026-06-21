from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from framework import ParseContext, ZoneParseGraph, build_zone_parse_graph, node_to_string
from synthetipy.ast_nodes import PropertyNode


def group_zones(zones_list: list[dict[str, str]]) -> list[dict[str, str | list[str]]]:
    order: list[str] = []
    groups: dict[str, list[str]] = {}
    for item in zones_list:
        zone_id = item.get("id") or item.get("zone") or ""
        icon = (item.get("icon") or "").strip()
        if icon not in groups:
            groups[icon] = []
            order.append(icon)
        if zone_id and zone_id not in groups[icon]:
            groups[icon].append(zone_id)
    return [
        {
            "icon": icon,
            "zones": groups[icon],
            "type": str(icon).replace("GFX_district_specialization_", ""),
        }
        for icon in order
    ]


def render_zone_generated_configs(
    context: ParseContext,
    graph: ZoneParseGraph | None = None,
) -> ZoneParseGraph:
    graph = graph or build_zone_parse_graph(context)
    ast = context.ast

    bca_zones_data = []
    for name, zone in ast["common/zones"].items():
        potential = ""
        zone_unlock = ""
        show_in_tech = ""
        for stat in zone.body.statements:
            if not isinstance(stat, PropertyNode):
                continue
            if str(stat.key) == "potential":
                potential = node_to_string(stat.value)
            elif str(stat.key) == "unlock":
                zone_unlock = node_to_string(stat.value)
            elif str(stat.key) == "show_in_tech":
                show_in_tech = node_to_string(stat.value)
        bca_zones_data.append(
            {
                "name": name,
                "potential": potential,
                "unlock": zone_unlock,
                "show_in_tech": show_in_tech,
            }
        )

    bca_districts_data = []
    always_uncapped_districts = []
    for name, district in ast["common/districts"].items():
        potential = ""
        allow = ""
        is_uncapped = ""
        for stat in district.body.statements:
            if not isinstance(stat, PropertyNode):
                continue
            if str(stat.key) == "potential":
                potential = node_to_string(stat.value)
            elif str(stat.key) == "allow":
                allow = node_to_string(stat.value)
            elif str(stat.key) == "is_uncapped":
                is_uncapped = node_to_string(stat.value)
        if not is_uncapped:
            always_uncapped_districts.append(name)
        bca_districts_data.append(
            {
                "name": name,
                "potential": potential,
                "allow": allow,
                "is_uncapped": is_uncapped,
            }
        )

    bca_zone_types_data = []
    for name, districts in graph.zone_to_districts.items():
        multi_zone_districts = [d for d in districts if graph.district_type_mapping.get(d) == "multi_zone"]
        single_zone_districts = [d for d in districts if graph.district_type_mapping.get(d) == "single_zone"]
        bca_zone_types_data.append(
            {
                "name": name,
                "multi_zone_districts": multi_zone_districts,
                "single_zone_districts": single_zone_districts,
            }
        )

    context.write_generated_yaml(
        "zone_build_conditions.yaml",
        {
            "bca_zones": bca_zones_data,
            "bca_districts": bca_districts_data,
            "bca_zone_types": bca_zone_types_data,
        },
    )

    used_districts = []
    used_district_set = set()
    for districts in graph.zone_to_districts.values():
        used_district_set.update(districts)
    for name in ast["common/districts"].keys():
        if name in used_district_set:
            used_districts.append(name)
    context.write_generated_yaml(
        "used_districts.yaml",
        {
            "all_districts": used_districts,
            "primary_districts": [d for d in used_districts if graph.district_type_mapping.get(d) == "multi_zone"],
            "secondary_districts": [d for d in used_districts if graph.district_type_mapping.get(d) == "single_zone"],
        },
    )

    context.write_generated_yaml("zones_on_district.yaml", graph.district_to_zones)
    context.write_generated_yaml("districts_for_zone.yaml", {"districts_for_zone": graph.zone_to_districts})

    secondary = {
        zone: [d for d in districts if graph.district_type_mapping.get(d) == "single_zone"]
        for zone, districts in graph.zone_to_districts.items()
    }
    secondary = {zone: districts for zone, districts in secondary.items() if districts}
    context.write_generated_yaml("secondary_districts_for_zone.yaml", {"secondary_districts_for_zone": secondary})

    primary = {
        zone: [d for d in districts if graph.district_type_mapping.get(d) == "multi_zone"]
        for zone, districts in graph.zone_to_districts.items()
    }
    primary = {zone: districts for zone, districts in primary.items() if districts}
    context.write_generated_yaml("primary_districts_for_zone.yaml", {"primary_districts_for_zone": primary})

    overlapping = set(secondary.keys()) & set(primary.keys())
    context.write_generated_yaml("overlapping_zones.yaml", {"overlapping_zones": list(overlapping)})

    zone_icon_list = []
    for name, zone in ast["common/zones"].items():
        icon = None
        for stat in zone.body.statements:
            if isinstance(stat, PropertyNode) and str(stat.key) == "icon":
                icon = stat.value
        icon_value = str(icon) if icon else ""
        if icon_value.startswith('"') and icon_value.endswith('"'):
            icon_value = icon_value[1:-1]
        zone_icon_list.append({"id": name, "icon": icon_value})

    zone_type_fitness_data = context.load_config("zone_type_fitness.yaml")
    zone_type_fitness = zone_type_fitness_data.get("zone_type_fitness", [])
    zone_type_fitness_map = {item["type"]: item for item in zone_type_fitness}

    grouped = {"icons_info": group_zones(zone_icon_list)}
    zone_type_for_zone = {
        zone: group["type"]
        for group in grouped["icons_info"]
        for zone in group["zones"]
    }

    for zone, availability in graph.zone_building_availability.items():
        availability["zone_type"] = zone_type_for_zone.get(zone, "")

    for building_set, availability in graph.zones_for_building_set.items():
        for zone_key, type_key in (("included_in", "included_in_types"), ("excluded_from", "excluded_from_types")):
            types = []
            for zone in availability.get(zone_key, []):
                zone_type = zone_type_for_zone.get(zone, "")
                if zone_type and zone_type not in types:
                    types.append(zone_type)
            if types:
                availability[type_key] = types

    context.write_generated_yaml(
        "zone_building_mapping.yaml",
        {
            "building_availability_for_zone": graph.zone_building_availability,
            "zones_for_building_set": graph.zones_for_building_set,
        },
    )

    filtered_groups = []
    for group in grouped["icons_info"]:
        fitness_info = zone_type_fitness_map.get(group["type"])
        if not fitness_info:
            print(f"Warning: No fitness info found for type '{group['type']}'")
            continue
        if fitness_info.get("fitness_trigger"):
            group["fitness_trigger"] = fitness_info["fitness_trigger"]
        if fitness_info.get("fitness"):
            group["fitness"] = fitness_info["fitness"]
        filtered_groups.append(group)

    type_order = [item["type"] for item in zone_type_fitness]
    filtered_groups.sort(
        key=lambda item: type_order.index(item["type"]) if item["type"] in type_order else len(type_order)
    )
    context.write_generated_yaml("zone_config.yaml", {"zones_info": filtered_groups})
    context.write_generated_yaml(
        "always_uncapped_districts.yaml",
        {"always_uncapped_districts": always_uncapped_districts},
    )

    return graph


def main() -> None:
    context = ParseContext.build()
    render_zone_generated_configs(context)


if __name__ == "__main__":
    main()
