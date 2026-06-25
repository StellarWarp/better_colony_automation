from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game_paths import GAME_ROOT
from synthetipy.ast_loadder import ASTLoader
from synthetipy.ast_nodes import BlockNode, ListNode, PropertyNode
from synthetipy.compiler import compile_ast


GENERATED_CONFIG_DIR = Path(__file__).resolve().parents[1] / "templates" / "generated_configs"
CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs"

COMMON_AST_CONFIG = {
    "common": {
        "districts",
        "pop_jobs",
        "zone_slots",
        "zones",
        "economic_categories",
    },
}


class NoAliasSafeDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.dump(
            payload,
            handle,
            Dumper=NoAliasSafeDumper,
            allow_unicode=True,
            sort_keys=False,
        )


def node_to_string(node) -> str:
    if not node:
        return ""
    if isinstance(node, BlockNode):
        return "\n".join(compile_ast(stmt) for stmt in node.statements)
    if isinstance(node, ListNode):
        return " ".join(compile_ast(item) for item in node.items)
    return compile_ast(node)


def list_node_values(node, field_name: str, object_name: str) -> list[str]:
    if not isinstance(node, ListNode):
        raise ValueError(f"Expected list for {field_name} in {object_name}")
    return [str(item) for item in node.items]


def iter_property_nodes(node):
    if node is None:
        return
    if isinstance(node, PropertyNode):
        yield node
        yield from iter_property_nodes(node.value)
        return
    if isinstance(node, BlockNode):
        for statement in node.statements:
            yield from iter_property_nodes(statement)
        return
    if isinstance(node, ListNode):
        for item in node.items:
            yield from iter_property_nodes(item)


@dataclass
class ParseContext:
    ast: dict[str, Any]
    generated_configs_dir: Path
    configs_dir: Path

    @classmethod
    def build(cls, ast_config: dict[str, Any] | None = None) -> "ParseContext":
        ast = ASTLoader(GAME_ROOT, ast_config or COMMON_AST_CONFIG).load()
        context = cls(
            ast=ast,
            generated_configs_dir=GENERATED_CONFIG_DIR,
            configs_dir=CONFIGS_DIR,
        )
        apply_blacklisted_districts(context)
        return context

    def load_config(self, filename: str) -> dict[str, Any]:
        return load_yaml(self.configs_dir / filename)

    def write_generated_yaml(self, filename: str, payload: dict[str, Any]) -> None:
        write_yaml(self.generated_configs_dir / filename, payload)


@dataclass
class ZoneParseGraph:
    district_type_mapping: dict[str, str]
    zone_slot_to_districts: dict[str, list[str]]
    zone_set_to_zone_slots: dict[str, list[str]]
    zone_to_zone_sets: dict[str, list[str]]
    zone_to_districts: dict[str, list[str]]
    district_to_zones: dict[str, list[str]]
    zone_building_availability: dict[str, dict[str, list[str] | str]]
    zones_for_building_set: dict[str, dict[str, list[str]]]


def apply_blacklisted_districts(context: ParseContext) -> None:
    blacklisted = set(
        context.load_config("blacklisted_secondary_districts.yaml").get("blacklisted_districts", [])
    )
    if not blacklisted:
        return

    districts_ast = dict(context.ast["common/districts"])
    for district in list(districts_ast.keys()):
        if district in blacklisted:
            del districts_ast[district]
    context.ast["common/districts"] = districts_ast


def build_zone_parse_graph(context: ParseContext) -> ZoneParseGraph:
    ast = context.ast
    districts_ast = dict(ast["common/districts"])

    district_type_mapping: dict[str, str] = {}
    zone_slot_to_districts: dict[str, list[str]] = {}
    for name, district in districts_ast.items():
        for stat in district.body.statements:
            if not isinstance(stat, PropertyNode) or str(stat.key) != "zone_slots":
                continue
            values = list_node_values(stat.value, "zone_slots", name)
            for zone_slot in values:
                zone_slot_to_districts.setdefault(zone_slot, []).append(name)
            district_type_mapping[name] = "single_zone" if len(values) == 1 else "multi_zone"

    zone_set_to_zone_slots: dict[str, list[str]] = {}
    for name, zone_slot in ast["common/zone_slots"].items():
        for stat in zone_slot.body.statements:
            if not isinstance(stat, PropertyNode) or str(stat.key) != "included_zone_sets":
                continue
            for zone_set in list_node_values(stat.value, "included_zone_sets", name):
                zone_set_to_zone_slots.setdefault(zone_set, []).append(name)

    zone_to_zone_sets: dict[str, list[str]] = {}
    for name, zone in ast["common/zones"].items():
        for stat in zone.body.statements:
            if not isinstance(stat, PropertyNode) or str(stat.key) != "zone_sets":
                continue
            zone_to_zone_sets[name] = list_node_values(stat.value, "zone_sets", name)
    zone_to_zone_sets.pop("zone_default", None)

    zone_building_availability: dict[str, dict[str, list[str] | str]] = {}
    zones_for_building_set: dict[str, dict[str, list[str]]] = {}
    zone_building_fields = {
        "include": "included_buildings",
        "exclude": "excluded_buildings",
        "included_building_sets": "included_building_sets",
        "excluded_building_sets": "excluded_building_sets",
    }
    for name, zone in ast["common/zones"].items():
        availability: dict[str, list[str] | str] = {}
        for stat in zone.body.statements:
            if not isinstance(stat, PropertyNode):
                continue
            output_name = zone_building_fields.get(str(stat.key))
            if not output_name:
                continue
            values = list_node_values(stat.value, str(stat.key), name)
            if values:
                availability[output_name] = values
        if not availability:
            continue
        zone_building_availability[name] = availability
        for building_set in availability.get("included_building_sets", []):
            zones_for_building_set.setdefault(building_set, {}).setdefault("included_in", []).append(name)
        for building_set in availability.get("excluded_building_sets", []):
            zones_for_building_set.setdefault(building_set, {}).setdefault("excluded_from", []).append(name)

    zone_to_districts: dict[str, list[str]] = {}
    for zone, zone_sets in zone_to_zone_sets.items():
        for zone_set in zone_sets:
            zone_slots = zone_set_to_zone_slots.get(zone_set)
            if not zone_slots:
                print(f"Zone set [{zone_set}] has no associated zone slots")
                continue
            for zone_slot in zone_slots:
                districts = zone_slot_to_districts.get(zone_slot)
                if not districts:
                    print(f"Zone slot [{zone_slot}] has no associated districts")
                    continue
                zone_to_districts.setdefault(zone, []).extend(districts)

    district_to_zones: dict[str, list[str]] = {}
    for zone, districts in zone_to_districts.items():
        for district in districts:
            district_to_zones.setdefault(district, []).append(zone)
    return ZoneParseGraph(
        district_type_mapping=district_type_mapping,
        zone_slot_to_districts=zone_slot_to_districts,
        zone_set_to_zone_slots=zone_set_to_zone_slots,
        zone_to_zone_sets=zone_to_zone_sets,
        zone_to_districts=zone_to_districts,
        district_to_zones=district_to_zones,
        zone_building_availability=zone_building_availability,
        zones_for_building_set=zones_for_building_set,
    )
