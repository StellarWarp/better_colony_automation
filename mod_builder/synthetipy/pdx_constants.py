"""
PDX 语言常量定义

集中管理 PDX 脚本语言的关键字、操作符、文件类型等常量
避免在各个模块中重复定义

注意:trigger/effect 等游戏元素的标识符在 game_rules 模块中(自动生成)
"""

# ============================================
# 逻辑操作符
# ============================================

LOGIC_OPERATORS = frozenset({'AND', 'OR', 'NOT', 'NOR', 'NAND'})


# ============================================
# 比较操作符映射 (PDX -> Python)
# ============================================

COMPARISON_OPS = {
    '=': '==',
    '>': '>',
    '<': '<',
    '>=': '>=',
    '<=': '<=',
    '==': '==',
    '!=': '!='
}


# ============================================
# 文件类型规则
# ============================================

FILE_TYPE_RULES = {
    'common/scripted_triggers': 'trigger',
    'common/scripted_effects': 'effect',
    'common/script_values': 'value',
    'common/buildings': 'object',
    'common/districts': 'object',
    'common/technologies': 'object',
    'common/technology': 'object',
    'common/edicts': 'object',
    'common/decisions': 'object',
    'common/traits': 'object',
    'common/ship_sizes': 'object',
    'common/component_templates': 'object',
    'common/scripted_modifiers': 'object',
    'common/static_modifiers': 'object',
    'common/ascension_perks': 'object',
    'common/policies': 'object',
    'events': 'event',
}


# ============================================
# 保留常量（向后兼容，计划逐步迁移到 game_rules）
# ============================================
# 注意:完整的游戏规则在 game_rules 模块中(从游戏文档自动生成)
# 这些常量将逐步弃用，使用 game_rules 中的精确规则替代

# 迭代作用域（计划迁移到 game_rules）
ITERATION_SCOPES = {
    'any_owned_planet': ('planet', 'owned_planets'),
    'every_owned_planet': ('planet', 'owned_planets'),
    'any_owned_pop': ('pop', 'owned_pops'),
    'every_owned_pop': ('pop', 'owned_pops'),
    'any_planet': ('planet', 'planets'),
    'every_planet': ('planet', 'planets'),
    'any_pop': ('pop', 'pops'),
    'every_pop': ('pop', 'pops'),
    'any_country': ('country', 'countries'),
    'every_country': ('country', 'countries'),
    'any_owned_fleet': ('fleet', 'owned_fleets'),
    'every_owned_fleet': ('fleet', 'owned_fleets'),
}


# 变量和标记操作（计划用 game_rules 替代）
VARIABLE_OPS = frozenset({
    'set_variable', 'add_variable', 'subtract_variable', 
    'multiply_variable', 'divide_variable', 'clear_variable',
    'change_variable',
})

FLAG_OPS = frozenset({
    'set_planet_flag', 'remove_planet_flag',
    'set_country_flag', 'remove_country_flag',
    'set_global_flag', 'remove_global_flag',
    'set_star_flag', 'remove_star_flag',
    'set_fleet_flag', 'remove_fleet_flag',
    'set_ship_flag', 'remove_ship_flag',
    'set_pop_flag', 'remove_pop_flag',
    'set_leader_flag', 'remove_leader_flag',
})

# 带参数块的效果（计划用 game_rules 替代）
BLOCK_EFFECTS = frozenset({
    'add_modifier', 'remove_modifier',
    'add_building', 'remove_building',
    'add_district', 'remove_district',
    'add_resource', 'fire_event', 'send_message',
    'create_pop', 'kill_pop',
    'create_fleet', 'create_ship',
    'create_army', 'create_leader',
    'set_owner', 'set_controller',
    'add_deposit', 'remove_deposit',
    'add_trait', 'remove_trait',
})

# 特殊调用关键字（计划用 game_rules 替代）
SPECIAL_CALLS = frozenset({
    'check_variable_arithmetic',
    'check_variable',
    'custom_tooltip',
    'custom_tooltip_with_fail_root',
    'hidden_tooltip',
})

# 作用域类型
SCOPE_TYPES = {
    'country': {'owner', 'from', 'root', 'prev', 'controller', 'overlord'},
    'planet': {'capital', 'home_planet', 'capital_planet'},
    'pop': {'pop', 'species'},
    'leader': {'ruler', 'leader'},
    'fleet': {'fleet'},
    'ship': {'ship'},
    'system': {'solar_system'},
    'sector': {'sector'},
}


# ============================================
# 词法分析关键字
# ============================================

LEXER_KEYWORDS = LOGIC_OPERATORS


PYTHON_RESERVED_WORDS = frozenset({
    'from',
    'class', 
    'def', 
    'lambda',
    'pass',
    'global',
    'nonlocal',
    'assert',
    'yield',
})


def safe_identifier(name: str) -> str:
    """Return a safe Python identifier for scope field names (avoid keywords)."""
    # Simple strategy: append underscore if name is a Python keyword
    # Keep minimal mapping for now
    if name in PYTHON_RESERVED_WORDS:
        return name + '_'
    return name


from synthetipy.game_definitions.identifiers import (
    EFFECT_IDENTIFIERS_EXCLUSIVE,
    TRIGGER_IDENTIFIERS_EXCLUSIVE,
    SHARED_IDENTIFIERS)

TRIGGER_IDENTIFIERS = TRIGGER_IDENTIFIERS_EXCLUSIVE.union(SHARED_IDENTIFIERS)
EFFECT_IDENTIFIERS = EFFECT_IDENTIFIERS_EXCLUSIVE.union(SHARED_IDENTIFIERS)

def is_trigger_identifier(name: str) -> bool:
    """Check if a name is a known trigger identifier."""
    return name in TRIGGER_IDENTIFIERS

def is_effect_identifier(name: str) -> bool:
    """Check if a name is a known effect identifier."""
    return name in EFFECT_IDENTIFIERS