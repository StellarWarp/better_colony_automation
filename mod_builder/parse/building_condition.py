from pathlib import Path
import sys

import yaml

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from synthetipy.ast_loadder import ASTLoader
    from synthetipy.ast_nodes import *
    from synthetipy.compiler import compile_ast
else:
    from ..synthetipy.ast_loadder import ASTLoader
    from ..synthetipy.ast_nodes import *
    from ..synthetipy.compiler import compile_ast


CONFIG = {
    'common': {
        "buildings"
    },
}

GAME_ROOT = Path(r"D:\SteamLibrary\steamapps\common\Stellaris")

ast = ASTLoader(GAME_ROOT, CONFIG).load()

def node_to_string(node):
    if not node: return ""
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

buildings_data = []

for name, zone in ast['common/buildings'].items():
    potential = ""
    allow = ""
    abort_trigger = ""
    prerequisites = None
    category = None
    building_sets = []
    upgrades = []
    for stat in zone.body.statements:
        if not isinstance(stat, PropertyNode): continue
        key = str(stat.key)
        if key == 'potential':
            potential = node_to_string(stat.value)
        elif key == 'allow':
            allow = node_to_string(stat.value)
        elif key == 'abort_trigger':
            abort_trigger = node_to_string(stat.value)
        elif key == 'prerequisites':
            prerequisites = prerequisites_to_data(stat.value)
        elif key == 'category':
            category = _node_to_source(stat.value)
        elif key == 'building_sets':
            building_sets = _node_to_string_items(stat.value)
        elif key == 'upgrades':
            upgrades = _node_to_string_items(stat.value)

    buildings_data.append({
        "name": str(zone.name.identifier),
        "category": category,
        "building_sets": building_sets,
        "upgrades": upgrades,
        "potential": potential,
        "allow": allow,
        "abort_trigger": abort_trigger,
        "prerequisites": prerequisites
    })

building_by_name = {item["name"]: item for item in buildings_data}


def _upgrade_chain_for(building_name, visiting=None):
    visiting = visiting or set()
    if building_name in visiting:
        return []
    visiting.add(building_name)

    chain = []
    for upgrade in building_by_name.get(building_name, {}).get("upgrades") or []:
        if upgrade in chain:
            continue
        chain.append(upgrade)
        for descendant in _upgrade_chain_for(upgrade, visiting):
            if descendant not in chain:
                chain.append(descendant)

    visiting.remove(building_name)
    return chain


for building in buildings_data:
    building["upgrade_chain"] = _upgrade_chain_for(building["name"])

with open("../templates/generated_configs/building_conditions.yaml", "w", encoding="utf-8") as f:
    yaml.dump({"bca_buildings": buildings_data}, f, allow_unicode=True, sort_keys=False)
