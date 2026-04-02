from typing import Any, List, Dict, Optional, Union
from abc import ABC, abstractmethod
from .ast_nodes import *  # Import all AST node classes

# ============================================
# 辅助类
# ============================================

class ASTVisitor(ABC):
    """访问者模式基类 - 用于遍历 AST"""
    
    def visit_document(self, node: DocumentNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_object(self, node: ObjectNode):
        node.body.accept(self)
    
    def visit_property(self, node: PropertyNode):
        node.value.accept(self)
    
    def visit_block(self, node: BlockNode):
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_literal(self, node: LiteralNode):
        pass
    
    # Backward compatibility alias
    def visit_value(self, node: LiteralNode):
        return self.visit_literal(node)
    
    def visit_list(self, node: ListNode):
        for item in node.items:
            item.accept(self)
    
    def visit_condition(self, node: ConditionNode):
        node.body.accept(self)
    
    def visit_comparison(self, node: ComparisonNode):
        node.right.accept(self)
    
    def visit_inline_script(self, node: InlineScriptNode):
        pass
    
    def visit_comment(self, node: CommentNode):
        pass
    
    def visit_directive(self, node: DirectiveNode):
        pass
    
    def visit_constant(self, node: ConstantNode):
        pass
    
    def visit_macro_parameter(self, node):
        pass
    
    def visit_macro_identifier(self, node):
        # 废弃方法，向后兼容
        pass
    
    def visit_scripted_value_call(self, node):
        # 废弃方法，向后兼容
        pass
    
    def visit_identifier_expression(self, node: IdentifierExpressionNode):
        pass
    
    def visit_inline_arithmetic(self, node: InlineArithmeticNode):
        pass
    
    def visit_conditional_param(self, node: ConditionalParamNode):
        for stmt in node.body:
            stmt.accept(self)
    
    def visit_constant_definition(self, node: ConstantDefinitionNode):
        node.value.accept(self)


class ASTTransformer(ASTVisitor):
    """AST 转换器 - 用于修改 AST"""
    
    def transform(self, node: ASTNode) -> ASTNode:
        """转换节点（可以返回新节点或修改后的节点）"""
        return node
    
    def visit_document(self, node: DocumentNode):
        node.statements = [
            self.transform(stmt.accept(self)) 
            for stmt in node.statements
        ]
        return node
    
    def visit_object(self, node: ObjectNode):
        node.body = self.transform(node.body.accept(self))
        return node
    
    def visit_property(self, node: PropertyNode):
        node.value = self.transform(node.value.accept(self))
        return node
    
    def visit_block(self, node: BlockNode):
        node.statements = [
            self.transform(stmt.accept(self))
            for stmt in node.statements
        ]
        return node
    
    # 其他 visit 方法类似...


# ============================================
# 便捷函数
# ============================================

def create_property(key: str, value: Any) -> PropertyNode:
    """创建属性节点"""
    if isinstance(value, ASTNode):
        return PropertyNode(key, value)
    elif isinstance(value, dict):
        return PropertyNode(key, dict_to_block(value))
    elif isinstance(value, list):
        return PropertyNode(key, ListNode([LiteralNode(v) for v in value]))
    else:
        return PropertyNode(key, LiteralNode(value))


def dict_to_block(data: Dict[str, Any]) -> BlockNode:
    """将 Python 字典转换为 Block 节点"""
    statements = []
    for key, value in data.items():
        statements.append(create_property(key, value))
    return BlockNode(statements)


def block_to_dict(block: BlockNode) -> Dict[str, Any]:
    """将 Block 节点转换为 Python 字典"""
    result = {}
    for stmt in block.statements:
        if isinstance(stmt, PropertyNode):
            key = str(stmt.key)
            if isinstance(stmt.value, BlockNode):
                result[key] = block_to_dict(stmt.value)
            elif isinstance(stmt.value, LiteralNode):
                result[key] = stmt.value.value
            elif isinstance(stmt.value, ListNode):
                result[key] = [item.value for item in stmt.value.items]
    return result
