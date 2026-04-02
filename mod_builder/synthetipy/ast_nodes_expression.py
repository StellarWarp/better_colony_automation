
"""
PDXLang Expression AST Nodes - 表达式相关的 AST 节点

完全重构的表达式系统，支持：
1. 结构化表达式（scope.identifier, scope.call）
2. 宏表达式（tech_$AREA$_1 等混合宏的表达式）
"""

from typing import List, Tuple, Optional, Any
from .ast_nodes_basic import ASTNode
import re


# ============================================
# 数据结构（非 ASTNode）
# ============================================

class MacroParam:
    """宏参数（可能有默认值）
    
    表示脚本中的宏参数，格式为 $PARAM$ 或 $PARAM|default$
    例如:
        $AREA$ -> MacroParam('AREA')
        $ID|none$ -> MacroParam('ID', 'none')
    """
    
    def __init__(self, param_str: str):
        """从参数字符串初始化（不含 $ 符号）
        
        Args:
            param_str: 参数字符串，如 "AREA" 或 "ID|none"
        """
        if '|' in param_str:
            parts = param_str.split('|', 1)
            self.name = parts[0]
            self.default = parts[1] if len(parts) > 1 else None
        else:
            self.name = param_str
            self.default = None
    
    def to_source(self) -> str:
        """转换回 PDXLang 源代码"""
        if self.default:
            return f"${self.name}|{self.default}$"
        return f"${self.name}$"
    
    def __str__(self):
        return self.to_source()
    
    def __repr__(self):
        if self.default:
            return f"MacroParam('{self.name}', default='{self.default}')"
        return f"MacroParam('{self.name}')"


class MacroExpression:
    """宏表达式数据结构
    
    用于表示包含宏参数的复杂表达式，不进行结构化解析
    例如：tech_$AREA$_1, $FROM$.capital, $PARAM$
    
    保留原始表达式文本，并提取其中的宏参数列表
    """
    
    def __init__(self, raw_expression: str):
        """
        Args:
            raw_expression: 原始表达式字符串，如 "tech_$AREA$_1"
        """
        self.raw_expression = raw_expression
        self.macro_params = self._extract_macros()
    
    def _extract_macros(self) -> List[MacroParam]:
        """从表达式中提取所有宏参数"""
        pattern = r'\$([^$]+)\$'
        matches = re.findall(pattern, self.raw_expression)
        return [MacroParam(m) for m in matches]
    
    def to_source(self) -> str:
        """序列化回 PDXLang"""
        return self.raw_expression
    
    def __repr__(self):
        return f"MacroExpr('{self.raw_expression}', params={[p.name for p in self.macro_params]})"
    
    def __str__(self):
        return self.raw_expression


class CallInfo:
    """调用信息数据结构（非 ASTNode）
    
    表示特殊调用的信息：value:, trigger:, modifier:
    
    注意：arguments 是键值对列表，不是简单列表
    例如：value:tech_cost|AREA|physics|
    -> arguments = [("AREA", "physics")]
    """
    
    def __init__(self, call_type: str, function_name: str, arguments: Optional[List[Tuple[str, Any]]] = None):
        """
        Args:
            call_type: 调用类型，如 'value', 'trigger', 'modifier'
            function_name: 函数名
            arguments: 参数键值对列表，值可以是 str, MacroParam 等
        """
        self.call_type = call_type
        self.function_name = function_name
        self.arguments = arguments or []
    
    def to_source(self) -> str:
        """序列化回 PDXLang"""
        args_str = ''
        if self.arguments:
            # 展开键值对
            parts = []
            for key, value in self.arguments:
                parts.append(str(key))
                parts.append(str(value))
            args_str = '|' + '|'.join(parts) + '|'
        
        return f"{self.call_type}:{self.function_name}{args_str}"
    
    def __repr__(self):
        return f"CallInfo({self.call_type}:{self.function_name}, args={self.arguments})"
    
    def __str__(self):
        return self.to_source()


# ============================================
# AST 节点
# ============================================

class IdentifierNode(ASTNode):
    """标识符节点：name@[scope_binding]
    
    表示纯标识符，可能带有 scope binding
    例如：
        variable_name
        variable_name@prev
        variable_name@owner  (scope_binding 是递归解析的 ScopeNode)
    """
    
    def __init__(self, name: str, scope_binding: Optional['ScopeNode'] = None):
        super().__init__()
        self.name = name
        self.scope_binding = scope_binding  # 递归：可以是复杂的 scope 表达式
        
        if scope_binding and isinstance(scope_binding, ASTNode):
            scope_binding.parent = self
    
    def to_source(self) -> str:
        """序列化回 PDXLang"""
        if self.scope_binding:
            return f"{self.name}@{self.scope_binding.to_source()}"
        return self.name
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_identifier(self)
    
    def __repr__(self):
        if self.scope_binding:
            return f"Identifier('{self.name}@{self.scope_binding}')"
        return f"Identifier('{self.name}')"
    
    def __str__(self):
        return self.to_source()


class ScopeObjectNode(ASTNode):
    """单个 Scope 对象节点
    
    表示单个 scope：owner, planet, capital_scope 等
    这是 Scope 链的基本单元
    """
    
    def __init__(self, scope_name: str):
        super().__init__()
        self.scope_name = scope_name
    
    def to_source(self) -> str:
        """序列化回 PDXLang"""
        return self.scope_name
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_scope_object(self)
    
    def __repr__(self):
        return f"ScopeObject('{self.scope_name}')"
    
    def __str__(self):
        return self.scope_name


class EventTargetNode(ScopeObjectNode):
    """Event Target 节点：event_target:identifier
    
    继承自 ScopeObjectNode，scope_name 初始化为 'event_target'
    target 是 IdentifierNode，可以是简单名称或包含宏的表达式
    
    例如：
        event_target:federation_leader
        event_target:$TARGET_NAME$
    """
    
    def __init__(self, target: IdentifierNode):
        super().__init__('event_target')  # 初始化 scope_name 为 'event_target'
        self.target = target
        target.parent = self
    
    def to_source(self) -> str:
        """序列化回 PDXLang"""
        return f"event_target:{self.target.name}"
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_event_target(self)
    
    def __repr__(self):
        return f"EventTarget({self.target.name})"
    
    def __str__(self):
        return self.to_source()


class ScopeNode(ASTNode):
    """Scope 链节点（原 ScopeNode）
    
    表示连续的 Scope 访问链：owner.overlord.capital_scope
    
    scopes 可以包含 ScopeObjectNode 和 EventTargetNode
    例如：
        owner.overlord
        event_target:leader.owner
    """
    
    def __init__(self, scopes: List[ScopeObjectNode]):
        super().__init__()
        self.scopes = scopes
        for scope in scopes:
            scope.parent = self
    
    def to_source(self) -> str:
        """序列化回 PDXLang"""
        return '.'.join(s.to_source() for s in self.scopes)
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_scope(self)
    
    def __repr__(self):
        chain = '.'.join(s.scope_name for s in self.scopes)
        return f"Scope('{chain}')"
    
    def __str__(self):
        return self.to_source()


class IdentifierExpressionNode(ASTNode):
    """统一表达式节点（完全重构）
    
    两种互斥模式：
    
    模式1 - 结构化表达式（不含宏混合）：
        - 单独 scope: 
            - owner.overlord
            - event_target:$TARGET$
          使用：scope
        - 属性访问: 
            - owner.variable_name@prev
            - event_target:$TARGET$.variable_name
            - owner.variable_name@event_target:$TARGET$
          使用：scope + identifier
        - 调用表达式: 
            - owner.value:tech_cost|AREA|physics|
            - owner.value:tech_cost|AREA|$PARAM$| 
          使用：scope + call_info
    
    模式2 - 宏表达式（包含宏混合）：
        - tech_$AREA$_1 (混合宏)
        - $FROM$.capital (宏开头的链)
        - owner.$PARAM$ (中间或尾部无法解析)
        - $PARAM$ (完整宏)
        使用：macro_expression
    
    判断方式：macro_expression is not None 则为宏表达式
    """
    
    def __init__(self):
        super().__init__()
        # 模式1：结构化（三者互斥使用）
        self.scope: Optional[ScopeNode] = None
        self.identifier: Optional[IdentifierNode] = None
        self.call_info: Optional[CallInfo] = None
        
        # 模式2：宏表达式
        self.macro_expression: Optional[MacroExpression] = None
    
    @property
    def is_macro_expression(self) -> bool:
        """判断是否为宏表达式模式"""
        return self.macro_expression is not None
    
    def to_source(self) -> str:
        """序列化回 PDXLang"""
        if self.is_macro_expression:
            return self.macro_expression.to_source()
        
        # 结构化模式
        parts = []
        if self.scope:
            parts.append(self.scope.to_source())
        if self.identifier:
            parts.append(self.identifier.to_source())
        if self.call_info:
            parts.append(self.call_info.to_source())
        
        return '.'.join(parts) if parts else ''
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_identifier_expression(self)
    
    def __repr__(self):
        if self.is_macro_expression:
            return f"IdentifierExpr(macro={self.macro_expression})"
        
        parts = []
        if self.scope:
            parts.append(f"scope={self.scope}")
        if self.identifier:
            parts.append(f"id={self.identifier}")
        if self.call_info:
            parts.append(f"call={self.call_info}")
        
        return f"IdentifierExpr({', '.join(parts)})"
    
    def __str__(self):
        return self.to_source()