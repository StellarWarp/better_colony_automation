"""
Synthetipy - 代码生成器/编译器
将 AST 编译回 PDXLang 脚本代码
"""

from typing import List, Optional, TextIO

from synthetipy.ast_nodes_expression import ScopeNode
from .ast_nodes import (
    ASTNode, DocumentNode, ObjectNode, PropertyNode, BlockNode, 
    LiteralNode, ListNode, ConditionNode, ComparisonNode, CommentNode,
    ConstantDefinitionNode, DirectiveNode, IdentifierExpressionNode,
    ConditionalParamNode, InlineArithmeticNode, InlineScriptNode
)


class Compiler:
    """将 AST 编译回 PDXLang 脚本"""
    
    def __init__(self, indent_size: int = 4, use_tabs: bool = False):
        """
        Args:
            indent_size: 缩进空格数
            use_tabs: 是否使用制表符缩进
        """
        self.indent_size = indent_size
        self.use_tabs = use_tabs
        self.indent_char = '\t' if use_tabs else ' ' * indent_size
        self.current_indent = 0
    
    def compile(self, node: ASTNode) -> str:
        """编译 AST 节点为字符串"""
        if isinstance(node, DocumentNode):
            return self._compile_document(node)
        elif isinstance(node, ObjectNode):
            return self._compile_object(node)
        elif isinstance(node, PropertyNode):
            return self._compile_property(node)
        elif isinstance(node, BlockNode):
            return self._compile_block(node)
        elif isinstance(node, ListNode):
            return self._compile_list(node)
        elif isinstance(node, ConditionNode):
            return self._compile_condition(node)
        elif isinstance(node, ComparisonNode):
            return self._compile_comparison(node)
        elif isinstance(node, LiteralNode):
            return self._compile_value(node)
        elif isinstance(node, ConstantDefinitionNode):
            return self._compile_constant_definition(node)
        elif isinstance(node, DirectiveNode):
            return self._compile_directive(node)
        elif isinstance(node, IdentifierExpressionNode):
            return self._compile_identifier_expression(node)
        elif isinstance(node, ScopeNode):
            return self._compile_scope(node)
        elif isinstance(node, ConditionalParamNode):
            return self._compile_conditional_param(node)
        elif isinstance(node, InlineArithmeticNode):
            return self._compile_inline_arithmetic(node)
        elif isinstance(node, InlineScriptNode):
            return self._compile_inline_script(node)
        elif isinstance(node, CommentNode):
            return self._compile_comment(node)
        else:
            raise NotImplementedError(f"Unsupported AST node type: {type(node).__name__}")
    
    def _get_indent(self) -> str:
        """获取当前缩进字符串"""
        return self.indent_char * self.current_indent
    
    def _compile_document(self, node: DocumentNode) -> str:
        """编译文档节点"""
        lines = []
        for stmt in node.statements:
            compiled = self.compile(stmt)
            if compiled:
                lines.append(compiled)
        return '\n\n'.join(lines)
    
    def _compile_object(self, node: ObjectNode) -> str:
        """编译对象定义"""
        indent = self._get_indent()
        name = node.name if not isinstance(node.name, ASTNode) else self.compile(node.name)
        body = self.compile(node.body)
        return f"{indent}{name} = {body}"

    def _compile_property(self, node: PropertyNode) -> str:
        """编译属性赋值"""
        indent = self._get_indent()
        key = node.key if not isinstance(node.key, ASTNode) else self.compile(node.key)

        # 如果 key 包含空格或特殊字符，可能需要加引号
        # 但在 PDXLang 中通常不需要

        value = self.compile(node.value)
        return f"{indent}{key} = {value}"
    
    def _compile_property(self, node: PropertyNode) -> str:
        """编译属性赋值"""
        indent = self._get_indent()
        key = node.key
        
        # 如果 key 包含空格或特殊字符，可能需要加引号
        # 但在 PDXLang 中通常不需要
        
        value = self.compile(node.value)
        return f"{indent}{key} = {value}"
    
    def _compile_block(self, node: BlockNode) -> str:
        """编译代码块"""
        if not node.statements:
            return "{ }"
        
        lines = ["{"]
        self.current_indent += 1
        
        for stmt in node.statements:
            compiled = self.compile(stmt)
            if compiled:
                lines.append(compiled)
        
        self.current_indent -= 1
        lines.append(self._get_indent() + "}")
        
        return '\n'.join(lines)
    
    def _compile_list(self, node: ListNode) -> str:
        """编译列表"""
        if not node.items:
            return "{ }"
        
        # 判断是否是简单列表（可以在一行内显示）
        all_simple = all(
            isinstance(item, (LiteralNode, IdentifierExpressionNode))
            for item in node.items
        )
        
        if all_simple and len(node.items) <= 1:
            # 简单列表，单行显示
            items_str = ' '.join(self.compile(item) for item in node.items)
            return f"{{ {items_str} }}"
        else:
            # 复杂列表，多行显示
            lines = ["{"]
            self.current_indent += 1
            
            for item in node.items:
                compiled = self.compile(item)
                if compiled:
                    lines.append(self._get_indent() + compiled)
            
            self.current_indent -= 1
            lines.append(self._get_indent() + "}")
            
            return '\n'.join(lines)
    
    def _compile_condition(self, node: ConditionNode) -> str:
        """编译逻辑条件"""
        indent = self._get_indent()
        operator = node.operator
        body = self.compile(node.body)
        return f"{indent}{operator} = {body}"
    
    def _compile_comparison(self, node: ComparisonNode) -> str:
        """编译比较表达式"""
        indent = self._get_indent()
        left = node.left
        operator = node.operator
        right = self.compile(node.right)
        return f"{indent}{left} {operator} {right}"
    
    def _compile_value(self, node: LiteralNode) -> str:
        """编译值节点"""
        return str(node)
            
    
    def _compile_constant_definition(self, node: ConstantDefinitionNode) -> str:
        """编译常量定义"""
        indent = self._get_indent()
        name = node.name
        value = self.compile(node.value)
        return f"{indent}{name} = {value}"
    
    def _compile_directive(self, node: DirectiveNode) -> str:
        """编译指令"""
        indent = self._get_indent()
        return f"{indent}{node.name}"
    
    def _compile_identifier_expression(self, node: IdentifierExpressionNode) -> str:
        """编译标识符表达式（使用 AST 节点自带序列化）"""
        # IdentifierExpressionNode 提供 to_source()，直接使用即可。
        return node.to_source()
    
    def _compile_scope(self, node: ScopeNode) -> str:
        """编译 scope 绑定"""
        # ScopeNode 提供 to_source()，直接使用即可。
        return node.to_source()
    
    def _compile_conditional_param(self, node: ConditionalParamNode) -> str:
        """编译条件参数块 [[PARAM] ... ]"""
        indent = self._get_indent()
        lines = [f"{indent}[[{node.param_name}]"]
        
        self.current_indent += 1
        for stmt in node.body:
            compiled = self.compile(stmt)
            if compiled:
                lines.append(compiled)
        self.current_indent -= 1
        
        lines.append(self._get_indent() + "]")
        
        return '\n'.join(lines)
    
    def _compile_inline_arithmetic(self, node: InlineArithmeticNode) -> str:
        """编译内联算术表达式"""
        if node.escaped:
            return f"@\\[{node.expression}]"
        else:
            return f"@[{node.expression}]"
    
    def _compile_inline_script(self, node: InlineScriptNode) -> str:
        """编译内联脚本
        无参数版本
        inline_script = "path/to/script"
        有参数版本
        inline_script = {
            script = "path/to/script"
            param1 = value1
            ...
        }
        
        """
        # 基本格式
        
        # 添加参数
        if node.parameters:
            result = self._get_indent() + "inline_script = {\n"
            self.current_indent += 1
            params = []
            for key, value in node.parameters.items():
                params.append(f"{key} = {self.compile(value) if isinstance(value, ASTNode) else value}")
            result += self._get_indent() + f"script = \"{node.script_path}\"\n"
            for param in params:
                result += self._get_indent() + param + "\n"
            self.current_indent -= 1
            result += self._get_indent() + "}"
            return result
        else:
            return self._get_indent() + f"inline_script = {node.script_path}"
        
        
    
    def _compile_comment(self, node: CommentNode) -> str:
        """编译注释"""
        indent = self._get_indent()
        return f"{indent}# {node.text}"
    
    def compile_to_file(self, node: ASTNode, filepath: str):
        """编译 AST 并写入文件"""
        code = self.compile(node)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)


def compile_ast(node: ASTNode, indent_size: int = 4, use_tabs: bool = False) -> str:
    """便捷函数：编译 AST 为字符串
    
    Args:
        node: AST 节点
        indent_size: 缩进空格数
        use_tabs: 是否使用制表符
    
    Returns:
        编译后的代码字符串
    """
    compiler = Compiler(indent_size=indent_size, use_tabs=use_tabs)
    return compiler.compile(node)


def compile_to_file(node: ASTNode, filepath: str, indent_size: int = 4, use_tabs: bool = False):
    """便捷函数：编译 AST 并写入文件
    
    Args:
        node: AST 节点
        filepath: 输出文件路径
        indent_size: 缩进空格数
        use_tabs: 是否使用制表符
    """
    compiler = Compiler(indent_size=indent_size, use_tabs=use_tabs)
    compiler.compile_to_file(node, filepath)
