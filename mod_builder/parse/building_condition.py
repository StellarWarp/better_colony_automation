from __future__ import annotations

from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from game_paths import GAME_ROOT
from synthetipy.ast_loadder import ASTLoader
from synthetipy.ast_nodes import (
    BlockNode,
    ComparisonNode,
    ConditionNode,
    IdentifierExpressionNode,
    InlineArithmeticNode,
    ListNode,
    LiteralNode,
    PropertyNode,
    ScopeNode,
)
from synthetipy.compiler import compile_ast


CONFIG = {
    "common": {
        "buildings",
    },
}

GENERATED_CONFIG_DIR = Path(__file__).resolve().parents[1] / "templates" / "generated_configs"


def node_to_string(node):
    if not node:
        return ""
    if isinstance(node, BlockNode):
        return "\n".join([compile_ast(stmt) for stmt in node.statements])
    elif isinstance(node, ListNode):
        return " ".join([compile_ast(item) for item in node.items])
    return compile_ast(node)


def _node_to_source(node):
    if isinstance(node, IdentifierExpressionNode):
        return node.to_source()
    if isinstance(node, ScopeNode):
        return node.to_source()
    if isinstance(node, LiteralNode):
        return str(node.value)
    return compile_ast(node)


def _node_to_string_items(node):
    if node is None:
        return []
    if isinstance(node, ListNode):
        return [_node_to_source(item) for item in node.items]
    if isinstance(node, BlockNode):
        items = []
        for stmt in node.statements:
            if isinstance(stmt, PropertyNode):
                items.append(str(stmt.key))
            else:
                items.append(_node_to_source(stmt))
        return items
    return [_node_to_source(node)]


def _prerequisite_children(node):
    if isinstance(node, BlockNode):
        return node.statements
    if isinstance(node, ListNode):
        return node.items
    return [node]


def _prerequisite_item_to_data(node):
    if isinstance(node, ConditionNode):
        return {
            "kind": "group",
            "operator": str(node.operator).lower(),
            "items": [
                item
                for item in (_prerequisite_item_to_data(child) for child in _prerequisite_children(node.body))
                if item is not None
            ],
        }

    if isinstance(node, PropertyNode):
        if str(node.key) == "has_technology":
            return {
                "kind": "tech",
                "name": _node_to_source(node.value),
            }

        return {
            "kind": "raw",
            "source": compile_ast(node),
        }

    if isinstance(node, (LiteralNode, IdentifierExpressionNode, ScopeNode, InlineArithmeticNode)):
        return {
            "kind": "tech",
            "name": _node_to_source(node),
        }

    if isinstance(node, ComparisonNode):
        return {
            "kind": "raw",
            "source": compile_ast(node),
        }

    if isinstance(node, (BlockNode, ListNode)):
        return {
            "kind": "group",
            "operator": "and",
            "items": [
                item
                for item in (_prerequisite_item_to_data(child) for child in _prerequisite_children(node))
                if item is not None
            ],
        }

    return {
        "kind": "raw",
        "source": compile_ast(node),
    }


def prerequisites_to_data(node):
    if not node:
        return None

    data = _prerequisite_item_to_data(node)
    if isinstance(data, dict) and data.get("kind") == "group" and not data.get("items"):
        return None
    return data


def _upgrade_chain_for(building_name, building_by_name, visiting=None):
    visiting = visiting or set()
    if building_name in visiting:
        return []
    visiting.add(building_name)

    chain = []
    for upgrade in building_by_name.get(building_name, {}).get("upgrades") or []:
        if upgrade in chain:
            continue
        chain.append(upgrade)
        for descendant in _upgrade_chain_for(upgrade, building_by_name, visiting):
            if descendant not in chain:
                chain.append(descendant)

    visiting.remove(building_name)
    return chain


def render_building_conditions() -> None:
    ast = ASTLoader(GAME_ROOT, CONFIG).load()
    buildings_data = []

    for _, building in ast["common/buildings"].items():
        potential = ""
        allow = ""
        abort_trigger = ""
        prerequisites = None
        category = None
        building_sets = []
        upgrades = []
        for stat in building.body.statements:
            if not isinstance(stat, PropertyNode):
                continue
            key = str(stat.key)
            if key == "potential":
                potential = node_to_string(stat.value)
            elif key == "allow":
                allow = node_to_string(stat.value)
            elif key == "abort_trigger":
                abort_trigger = node_to_string(stat.value)
            elif key == "prerequisites":
                prerequisites = prerequisites_to_data(stat.value)
            elif key == "category":
                category = _node_to_source(stat.value)
            elif key == "building_sets":
                building_sets = _node_to_string_items(stat.value)
            elif key == "upgrades":
                upgrades = _node_to_string_items(stat.value)

        buildings_data.append(
            {
                "name": str(building.name.identifier),
                "category": category,
                "building_sets": building_sets,
                "upgrades": upgrades,
                "potential": potential,
                "allow": allow,
                "abort_trigger": abort_trigger,
                "prerequisites": prerequisites,
            }
        )

    building_by_name = {item["name"]: item for item in buildings_data}
    for item in buildings_data:
        item["upgrade_chain"] = _upgrade_chain_for(item["name"], building_by_name)

    GENERATED_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with (GENERATED_CONFIG_DIR / "building_conditions.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump({"bca_buildings": buildings_data}, handle, allow_unicode=True, sort_keys=False)


if __name__ == "__main__":
    render_building_conditions()
