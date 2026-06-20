"""
PDXLang Statement Parser - 语句解析器

负责解析各种语句：
- 条件语句（OR, AND, NOT等）
- 属性和比较表达式
- 条件参数块
- 系统指令
"""

from typing import Union, Optional

from synthetipy.ast_nodes_basic import WrappedString
from .lexer import Token, TokenType
from .parser_utils import SYSTEM_DIRECTIVES
from ..ast_nodes import (
    ASTNode, PropertyNode, ComparisonNode, ConditionNode,
    ConditionalParamNode, DirectiveNode, BlockNode,
    LiteralNode, IdentifierExpressionNode, InlineScriptNode,
    ScopeNode
)


class StatementParserMixin:
    """语句解析器 Mixin
    
    提供语句解析相关的方法，设计为可被主 Parser 混入使用
    """
    
    def parse_statement(self) -> Optional[ASTNode]:
        """解析语句（在代码块内部）"""
        if self.is_at_end():
            return None
        
        # 条件参数块: [[PARAM] ... ]
        if self.check(TokenType.CONDITIONAL_PARAM):
            return self.parse_conditional_param()
        
        # 逻辑条件: OR = { ... }
        if self.is_logic_operator():
            return self.parse_condition()
        
        # 属性或比较: key = value (key 可以是标识符、数字或字符串)
        # 或系统指令: optimize_memory
        if self.check(TokenType.IDENTIFIER):
            # 检查是否是系统指令（单独的标识符，不带值）
            current_token = self.peek()
            identifier = current_token.value
            
            # 向前看，如果后面不是 = 或比较运算符，且是系统指令，则作为 Directive 处理
            next_token = self.peek_ahead(1)
            if identifier in SYSTEM_DIRECTIVES and next_token and next_token.type not in (
                TokenType.EQUALS, TokenType.GT, TokenType.LT,
                TokenType.GTE, TokenType.LTE, TokenType.EQUALS_EQUALS, TokenType.NOT_EQUALS,
                TokenType.DOT, TokenType.DIVIDE, TokenType.COLON, TokenType.AT
            ):
                # 这是一个系统指令
                self.advance()
                directive = DirectiveNode(identifier)
                directive.line = current_token.line
                directive.column = current_token.column
                return directive
            
            # 否则按普通属性/比较处理
            return self.parse_property_or_comparison()
        
        if self.check(TokenType.NUMBER):
            return self.parse_property_or_comparison()
        
        # 字符串作为键: "KEY" = value
        if self.check(TokenType.STRING):
            return self.parse_property_or_comparison()
        
        # 无法识别的语句
        current = self.peek()
        raise self.error(
            f"Unexpected token in statement",
            current,
            expected="IDENTIFIER, NUMBER, STRING, or logical operator",
            got=f"{current.type.name} '{current.value}'"
        )
    
    def parse_condition(self) -> ConditionNode:
        """解析逻辑条件块"""
        operator_token = self.advance()  # OR, AND, NOT, etc.
        operator = operator_token.value.upper()
        
        self.consume(TokenType.EQUALS, f"Expected '=' after '{operator}'")
        
        body = self.parse_block_or_list()
        
        condition = ConditionNode(operator, body)
        condition.line = operator_token.line
        condition.column = operator_token.column
        
        return condition
    
    def parse_conditional_param(self) -> ConditionalParamNode:
        """解析条件参数块 [[PARAM] ... ]"""
        param_token = self.advance()  # [[PARAM]
        param_value = param_token.value  # 例如 "[[SPIRITUALIST]"
        
        # 提取参数名（去掉 [[ 和 ]）
        param_name = param_value[2:-1]  # "[[SPIRITUALIST]" -> "SPIRITUALIST"
        
        # 跳过 [[PARAM] 后的换行
        self.skip_newlines()
        
        # 读取到匹配的 ] 为止的所有语句
        body = []
        while not self.is_at_end() and not self.check(TokenType.RBRACKET):
            self.skip_newlines()  # 跳过语句之间的换行
            if self.check(TokenType.RBRACKET):
                break
            stmt = self.parse_statement()
            if stmt is not None:
                body.append(stmt)
        
        # 消费结束的 ]
        self.consume(TokenType.RBRACKET, f"Expected ']' to close conditional param '[[{param_name}]'")
        
        conditional = ConditionalParamNode(param_name, body)
        conditional.line = param_token.line
        conditional.column = param_token.column
        
        return conditional
    
    def parse_property_or_comparison(self) -> Union[PropertyNode, ComparisonNode]:
        """解析属性或比较表达式
        
        数字和字符串也可以作为键：0 = value, "KEY" = value
        """
        # # 特殊情况：字符串作为键（例如 "MIN" = $MIN$）
        # if self.check(TokenType.STRING):
        #     str_token = self.advance()
        #     key_str = str_token.value
            
        #     # 字符串键通常只用于赋值，不支持比较运算符
        #     self.consume(TokenType.EQUALS, f"Expected '=' after string key '{key_str}'")
        #     value = self.parse_value()
            
        #     prop = PropertyNode(key_str, value)
        #     prop.line = str_token.line
        #     prop.column = str_token.column
        #     return prop
        
        # # 特殊情况：数字作为键（例如 traits = { 0 = value }）
        # if self.check(TokenType.NUMBER):
        #     num_token = self.advance()
        #     key_str = num_token.value
            
        #     # 检查比较运算符
        #     if self.check(TokenType.GT) or self.check(TokenType.LT) or \
        #        self.check(TokenType.GTE) or self.check(TokenType.LTE) or \
        #        self.check(TokenType.EQUALS_EQUALS) or self.check(TokenType.NOT_EQUALS):
        #         op_token = self.advance()
        #         operator = self.get_operator_string(op_token.type)
        #         right = self.parse_value()
                
        #         comparison = ComparisonNode(WrappedString(key_str), operator, right)
        #         comparison.line = num_token.line
        #         comparison.column = num_token.column
        #         return comparison
            
        #     # 普通属性赋值
        #     self.consume(TokenType.EQUALS, f"Expected '=' or comparison operator after '{key_str}'")
        #     value = self.parse_value()
            
        #     prop = PropertyNode(key_str, value)
        #     prop.line = num_token.line
        #     prop.column = num_token.column
        #     return prop
        
        # 正常情况：解析左值（更严格）
        key_node = self.parse_lvalue()
        
        # 从节点中提取键名
        if isinstance(key_node, IdentifierExpressionNode):
            # 使用统一序列化方法作为 key
            key_str = key_node.to_source()
        elif isinstance(key_node, ScopeNode):
            key_str = key_node.to_source()
        elif isinstance(key_node, LiteralNode):
            # LiteralNode
            key_str = str(key_node)
        else:
            raise self.error(
                "Invalid left-hand side in property or comparison",
                expected="identifier expression or value",
                got=f"{type(key_node).__name__}"
            )
        
        # 检查比较运算符（>= <= == != > <）
        if self.check(TokenType.GT) or self.check(TokenType.LT) or \
           self.check(TokenType.GTE) or self.check(TokenType.LTE) or \
           self.check(TokenType.EQUALS_EQUALS) or self.check(TokenType.NOT_EQUALS):
            op_token = self.advance()
            operator = self.get_operator_string(op_token.type)
            
            # 解析右值
            right = self.parse_value()
            
            comparison = ComparisonNode(key_node, operator, right)
            comparison.line = key_node.line
            comparison.column = key_node.column
            
            return comparison
        
        # 检查：如果是宏表达式（包含 $）且后面是结束符，允许单独成行
        # 例如：[[PARAM] $MACRO_VAR$ ]
        if '$' in key_str and (self.check(TokenType.NEWLINE) or self.check(TokenType.RBRACKET) or self.check(TokenType.RBRACE)):
            # 宏表达式可以作为独立语句，直接返回表达式节点
            return key_node
        
        # 普通属性赋值: key = value
        self.consume(TokenType.EQUALS, f"Expected '=' or comparison operator after '{key_str}'")
        
        value = self.parse_value()
        
        # TODO 这部分逻辑移动到二次解析中，在这里先生成普通属性节点
        # 特殊处理：如果是 inline_script，生成 InlineScriptNode
        # if key_str == 'inline_script':
        #     script_path, params = self._extract_inline_script_info(value)
        #     if script_path:
        #         inline_script = InlineScriptNode(script_path, params)
        #         inline_script.line = key_node.line
        #         inline_script.column = key_node.column
        #         value = inline_script
        
        prop = PropertyNode(key_node, value)
        prop.line = key_node.line
        prop.column = key_node.column
        
        return prop
    
    def get_operator_string(self, token_type: TokenType) -> str:
        """将 TokenType 转换为运算符字符串"""
        mapping = {
            TokenType.EQUALS: '=',
            TokenType.GT: '>',
            TokenType.LT: '<',
            TokenType.GTE: '>=',
            TokenType.LTE: '<=',
            TokenType.EQUALS_EQUALS: '==',
            TokenType.NOT_EQUALS: '!=',
        }
        return mapping.get(token_type, '=')
    
    def _extract_inline_script_info(self, value: ASTNode) -> tuple:
        """Extract script path and parameters from inline_script value
        
        Args:
            value: The value node (either LiteralNode for simple form or BlockNode for complex form)
            
        Returns:
            (script_path, params) tuple
        """
        script_path = None
        params = {}
        
        # Simple form: inline_script = jobs/researcher_add
        if isinstance(value, (LiteralNode, IdentifierExpressionNode)):
            if isinstance(value, LiteralNode):
                script_path = value.value
            else:
                script_path = value.to_source()
        
        # Complex form: inline_script = { script = ... PARAM = value }
        elif isinstance(value, BlockNode):
            for stmt in value.statements:
                if isinstance(stmt, PropertyNode):
                    key = str(stmt.key)
                    
                    if key == 'script':
                        # Extract script path
                        assert isinstance(stmt.value, LiteralNode)
                        script_path = stmt.value
                    else:
                        params[key] = stmt.value
        
        return script_path, params
