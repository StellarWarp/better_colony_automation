import copy
import yaml
from synthetipy.parser import parse
from synthetipy.ast_loadder import ASTLoader
from synthetipy.ast_nodes import *
from pathlib import Path
from synthetipy.compiler import compile_ast


CONFIG = {
    'common': {
        "buildings"
    },
}

GAME_ROOT = Path("D:\SteamLibrary\steamapps\common\Stellaris")

ast = ASTLoader(GAME_ROOT, CONFIG).load()

def node_to_string(node):
    if not node: return ""
    if isinstance(node, BlockNode):
        return "\n".join([compile_ast(stmt) for stmt in node.statements])
    elif isinstance(node, ListNode):
        return " ".join([compile_ast(item) for item in node.items])
    return compile_ast(node)

buildings_data = []

for name, zone in ast['common/buildings'].items():
    potential = ""
    allow = ""
    abort_trigger = ""
    prerequisites = []
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
            if isinstance(stat.value, ListNode):
                prerequisites = [compile_ast(item) for item in stat.value.items]
            elif isinstance(stat.value, BlockNode):
                prerequisites = [compile_ast(item.value) for item in stat.value.statements]

    buildings_data.append({
        "name": str(zone.name.identifier),
        "potential": potential,
        "allow": allow,
        "abort_trigger": abort_trigger,
        "prerequisites": prerequisites
    })

with open("../templates/generated_configs/building_conditions.yaml", "w", encoding="utf-8") as f:
    yaml.dump({"bca_buildings": buildings_data}, f, allow_unicode=True, sort_keys=False)



