from synthetipy.parser import parse
from synthetipy.script_merger import utils
from synthetipy.ast_loadder import ASTLoader
from synthetipy.ast_nodes import *
from pathlib import Path
import copy
import yaml
from synthetipy.compiler import compile_ast

CONFIG = {
    'common': {
        "districts",
        "zone_slots",
        "zones"
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

district_type_mapping = {}
# zone_slot -> List[district]
zone_slot_mapping: Dict[str, List[str]] = {}
for name, zone in ast['common/districts'].items():
    for stat in zone.body.statements:
        if not isinstance(stat, PropertyNode): continue
        if str(stat.key) == 'zone_slots':
            if not isinstance(stat.value, ListNode):
                raise ValueError(f"Expected list for zone_slots in district {name}")
            for zone_slot in stat.value.items:
                zone_slot_mapping.setdefault(str(zone_slot), []).append(name)
            if len(stat.value.items) == 1:
                district_type_mapping[name] = "single_zone"
            else:
                district_type_mapping[name] = "multi_zone"

# zone_set -> zone_slot
zone_set_zone_slot_mapping: Dict[str, List[str]] = {}
for name, zone in ast['common/zone_slots'].items():
    # zone_sets
    for stat in zone.body.statements:
        if not isinstance(stat, PropertyNode): continue
        if str(stat.key) == 'included_zone_sets':
            if not isinstance(stat.value, ListNode):
                raise ValueError(f"Expected list for zone_slots in zone {name}")
            for zone_set in stat.value.items:
                zone_set_zone_slot_mapping.setdefault(str(zone_set), []).append(name)

# zone -> zone_set
zone_zone_slot_mapping: Dict[str, List[str]] = {}
for name, zone in ast['common/zones'].items():
    # zone_sets
    for stat in zone.body.statements:
        if not isinstance(stat, PropertyNode): continue
        if str(stat.key) == 'zone_sets':
            if not isinstance(stat.value, ListNode):
                raise ValueError(f"Expected list for zone_slots in zone {name}")
            for zone_slot in stat.value.items:
                zone_zone_slot_mapping.setdefault(name, []).append(str(zone_slot))

zone_zone_slot_mapping.pop('zone_default', None)  # 移除默认的 zone_default

# zone -> List[district]
zone_district_mapping: Dict[str, List[str]] = {}
for zone, zone_sets in zone_zone_slot_mapping.items():
    for zone_set in zone_sets:
        zone_slots = zone_set_zone_slot_mapping.get(zone_set)
        if not zone_slots:
            print(f"Zone set [{zone_set}] has no associated zone slots")
            continue
        for zone_slot in zone_slots:
            districts = zone_slot_mapping.get(zone_slot)
            if not districts:
                print(f"Zone slot [{zone_slot}] has no associated districts")
                continue
            zone_district_mapping.setdefault(zone, []).extend(districts)


bca_zones_data = []

for name, zone in ast['common/zones'].items():
    potential = ""
    zone_unlock = ""
    show_in_tech = ""
    for stat in zone.body.statements:
        if not isinstance(stat, PropertyNode): continue
        if str(stat.key) == 'potential':
            potential = node_to_string(stat.value)
        elif str(stat.key) == 'unlock':
            zone_unlock = node_to_string(stat.value)
        elif str(stat.key) == 'show_in_tech':
            show_in_tech = node_to_string(stat.value)
    
    bca_zones_data.append({
        "name": name,
        "potential": potential,
        "unlock": zone_unlock,
        "show_in_tech": show_in_tech
    })

bca_districts_data = []
always_uncapped_districts = []

for name, districts in ast['common/districts'].items():
    potential = ""
    allow = ""
    is_uncapped = ""
    for stat in districts.body.statements:
        if not isinstance(stat, PropertyNode): continue
        if str(stat.key) == 'potential':
            potential = node_to_string(stat.value)
        elif str(stat.key) == 'allow':
            allow = node_to_string(stat.value)
        elif str(stat.key) == 'is_uncapped':
            is_uncapped = node_to_string(stat.value)
    if not is_uncapped:
        always_uncapped_districts.append(name)
    bca_districts_data.append({
        "name": name,
        "potential": potential,
        "allow": allow,
        "is_uncapped": is_uncapped
    })

bca_zone_types_data = []
for name in zone_district_mapping.keys():
    districts = zone_district_mapping.get(name, [])
    multi_zone_districts = [d for d in districts if district_type_mapping.get(d) == "multi_zone"]
    single_zone_districts = [d for d in districts if district_type_mapping.get(d) == "single_zone"]
    bca_zone_types_data.append({
        "name": name,
        "multi_zone_districts": multi_zone_districts,
        "single_zone_districts": single_zone_districts
    })

with open("../templates/generated_configs/zone_build_conditions.yaml", "w", encoding="utf-8") as f:
    yaml.dump({
        "bca_zones": bca_zones_data,
        "bca_districts": bca_districts_data,
        "bca_zone_types": bca_zone_types_data
    }, f, allow_unicode=True, sort_keys=False)

used_districts_set = set()
for zone, districts in zone_district_mapping.items():
    used_districts_set.update(districts)

used_districts_set_list = []
for name, district in ast['common/districts'].items():
    if name in used_districts_set:
        used_districts_set_list.append(name)
used_primary_districts_set_list = [name for name in used_districts_set_list if district_type_mapping.get(name) == "multi_zone" ]
used_secondary_districts_set_list = [name for name in used_districts_set_list if district_type_mapping.get(name) == "single_zone" ]

with open("../templates/generated_configs/used_districts.yaml", "w", encoding="utf-8") as f:
    yaml.dump({"all_districts": used_districts_set_list}, f, allow_unicode=True)
    yaml.dump({"primary_districts": used_primary_districts_set_list}, f, allow_unicode=True)
    yaml.dump({"secondary_districts": used_secondary_districts_set_list}, f, allow_unicode=True)

# district -> List[zone]
zones_on_district:Dict[str, List[str]] = {}

for zone, districts in zone_district_mapping.items():
    for district in districts:
        zones_on_district.setdefault(district, []).append(zone)

with open("../templates/generated_configs/zones_on_district.yaml", "w", encoding="utf-8") as f:
    yaml.dump(zones_on_district, f, allow_unicode=True)

with open("../templates/generated_configs/districts_for_zone.yaml", "w", encoding="utf-8") as f:
    yaml.dump({"districts_for_zone": zone_district_mapping}, f, allow_unicode=True)

# load manual_config/used_secondary_districts.yaml
with open("../configs/used_secondary_districts.yaml", "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
    used_secondary_districts = data.get("secondary_districts", [])

zone_district_mapping_single = {zone: [d for d in districts if district_type_mapping.get(d) == "single_zone" and d in used_secondary_districts] for zone, districts in zone_district_mapping.items()}
#remove empty entries
zone_district_mapping_single = {zone: districts for zone, districts in zone_district_mapping_single.items() if len(districts) > 0}
with open("../templates/generated_configs/secondary_districts_for_zone.yaml", "w", encoding="utf-8") as f:
    yaml.dump({"secondary_districts_for_zone": zone_district_mapping_single}, f, allow_unicode=True)

zone_district_mapping_multi = {zone: [d for d in districts if district_type_mapping.get(d) == "multi_zone"] for zone, districts in zone_district_mapping.items()}
#remove empty entries
zone_district_mapping_multi = {zone: districts for zone, districts in zone_district_mapping_multi.items() if len(districts) > 0}
with open("../templates/generated_configs/primary_districts_for_zone.yaml", "w", encoding="utf-8") as f:
    yaml.dump({"primary_districts_for_zone": zone_district_mapping_multi}, f, allow_unicode=True)

# overlapping_zone of zone_district_mapping_single and zone_district_mapping_multi
overlapping_zone = set(zone_district_mapping_single.keys()) & set(zone_district_mapping_multi.keys())
with open("../templates/generated_configs/overlapping_zones.yaml", "w", encoding="utf-8") as f:
    yaml.dump({"overlapping_zones": list(overlapping_zone)}, f, allow_unicode=True)

zone_icon_list = []
for name, zone in ast['common/zones'].items():
    icon = None
    for stat in zone.body.statements:
        if not isinstance(stat, PropertyNode): continue
        if str(stat.key) == 'icon':
            icon = stat.value

    icon = str(icon) if icon else None
    # icon may with "", remove them
    if icon and icon.startswith('"') and icon.endswith('"'):
        icon = icon[1:-1]
    zone_icon_list.append({"id": name, "icon": icon if icon else ""})

def group_zones(zones_list):
    order = []
    groups = {}
    for item in zones_list:
        zid = item.get('id') or item.get('zone') or ''
        icon = (item.get('icon') or '').strip()
        if icon not in groups:
            groups[icon] = []
            order.append(icon)
        if zid and zid not in groups[icon]:
            groups[icon].append(zid)
    return [{'icon': ic,
             'zones': groups[ic],
             'type': str(ic).replace('GFX_district_specialization_', '')
             }
            for ic in order]

with open("../configs/zone_type_fitness.yaml", "r", encoding="utf-8") as f:
    zone_type_fitness_data = yaml.safe_load(f) or {}

zone_type_fitness = zone_type_fitness_data.get('zone_type_fitness', [])
zone_type_fitness_map = {item['type']: item for item in zone_type_fitness}

grouped = {'icons_info': group_zones(zone_icon_list)}
group_to_remove = []
for group in grouped['icons_info']:
    type_ = group['type']
    fitness_info = zone_type_fitness_map.get(type_)
    if fitness_info:
        if fitness_info.get('fitness_trigger'):
            group['fitness_trigger'] = fitness_info.get('fitness_trigger')
        if fitness_info.get('fitness'):
            group['fitness'] = fitness_info.get('fitness')
    else:
        print(f"Warning: No fitness info found for type '{type_}'")
        group_to_remove.append(group)

for group in group_to_remove:
    grouped['icons_info'].remove(group)

type_order = [item['type'] for item in zone_type_fitness]
grouped['icons_info'].sort(key=lambda x: type_order.index(x['type']) if x['type'] in type_order else len(type_order))

grouped['zones_info'] = grouped.pop('icons_info')

with open("../templates/generated_configs/zone_config.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(grouped, f, sort_keys=False, allow_unicode=True, default_flow_style=False)

with open("../templates/generated_configs/always_uncapped_districts.yaml", "w", encoding="utf-8") as f:
    yaml.dump({"always_uncapped_districts": always_uncapped_districts}, f, allow_unicode=True)