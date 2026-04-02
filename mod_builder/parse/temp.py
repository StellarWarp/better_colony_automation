
import yaml


with open('../gui_generate/config/zone_config.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f) or {}

zone_configs = data.get('zones_info')
#remove icon and zones
for item in zone_configs:
    item.pop('icon', None)
    item.pop('zones', None)
with open('zone_type_fitness.yaml', 'w', encoding='utf-8') as f:
    yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, default_flow_style=False)