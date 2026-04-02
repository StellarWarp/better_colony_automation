"""
PDXLang Parser Context - 解析上下文

提供解析器需要的游戏规则数据，包括：
- Scope 标识符识别
- Trigger/Effect 标识符分类
- 其他游戏定义查询
"""

from typing import Set, Optional, Dict, Any
from ..game_definitions.identifiers import (
    SHARED_IDENTIFIERS,
    TRIGGER_IDENTIFIERS_EXCLUSIVE,
    EFFECT_IDENTIFIERS_EXCLUSIVE,
    SCOPES_IDENTIFIERS
)
from ..game_definitions.scope_rules import SCOPES


class ParserContext:
    """解析器上下文
    
    封装游戏规则数据，供解析器在语法分析阶段使用
    """
    
    def __init__(self, game_rules: Optional[Dict[str, Any]] = None):
        # Scope 标识符集合（保留原始类型，如 frozenset）
        self._scope_identifiers: Set[str] = SCOPES_IDENTIFIERS
        
        # Trigger 标识符（独占 + 共享）
        self._trigger_identifiers: Set[str] = TRIGGER_IDENTIFIERS_EXCLUSIVE | SHARED_IDENTIFIERS
        
        # Effect 标识符（独占 + 共享）
        self._effect_identifiers: Set[str] = EFFECT_IDENTIFIERS_EXCLUSIVE | SHARED_IDENTIFIERS
        
        # Scope 规则详细信息（复制以便修改）
        self._scope_rules: Dict[str, Dict[str, Any]] = dict(SCOPES)

        # 如果提供了自定义游戏规则（测试用途），使用它们进行覆盖/扩展
        if game_rules:
            if 'SCOPES' in game_rules:
                # 合并并更新 scope 列表（保持 _scope_identifiers 的原始不可变类型，通过创建新的 frozenset）
                self._scope_rules.update(game_rules['SCOPES'])
                self._scope_identifiers = self._scope_identifiers | frozenset(game_rules['SCOPES'].keys())
            # 未来可以支持触发器/效果等的自定义覆盖

    
    # ==================== Scope 相关 ====================
    
    def is_scope(self, identifier: str) -> bool:
        """判断标识符是否是 Scope
        
        Args:
            identifier: 要检查的标识符（如 'owner', 'capital_scope'）
        
        Returns:
            True 如果是有效的 scope 标识符
        """
        return identifier in self._scope_identifiers
    
    def get_scope_identifiers(self) -> Set[str]:
        """获取所有 Scope 标识符集合"""
        return self._scope_identifiers
    
    def get_scope_info(self, scope_name: str) -> Optional[Dict[str, Any]]:
        """获取 Scope 的详细信息
        
        Args:
            scope_name: Scope 名称
        
        Returns:
            Scope 规则字典，如果不存在返回 None
        """
        return self._scope_rules.get(scope_name)
    
    # ==================== 标识符分类 ====================
    
    def is_trigger_identifier(self, identifier: str) -> bool:
        """判断标识符是否是 Trigger 调用"""
        return identifier in self._trigger_identifiers
    
    def is_effect_identifier(self, identifier: str) -> bool:
        """判断标识符是否是 Effect 调用"""
        return identifier in self._effect_identifiers
    
    def is_shared_identifier(self, identifier: str) -> bool:
        """判断标识符是否在 Trigger 和 Effect 中共享"""
        return identifier in SHARED_IDENTIFIERS
    
    def get_identifier_type(self, identifier: str) -> Optional[str]:
        """获取标识符类型
        
        Returns:
            'scope' | 'trigger' | 'effect' | 'shared' | None
        """
        if self.is_scope(identifier):
            return 'scope'
        elif identifier in TRIGGER_IDENTIFIERS_EXCLUSIVE:
            return 'trigger'
        elif identifier in EFFECT_IDENTIFIERS_EXCLUSIVE:
            return 'effect'
        elif self.is_shared_identifier(identifier):
            return 'shared'
        return None
    
    # ==================== 辅助方法 ====================
    
    def __repr__(self):
        return (
            f"ParserContext("
            f"scopes={len(self._scope_identifiers)}, "
            f"triggers={len(self._trigger_identifiers)}, "
            f"effects={len(self._effect_identifiers)})"
        )


# 创建全局单例（可选，也可以每次实例化）
_global_context: Optional[ParserContext] = None


def get_parser_context() -> ParserContext:
    """获取全局解析器上下文（单例模式）"""
    global _global_context
    if _global_context is None:
        _global_context = ParserContext()
    return _global_context
