"""
PDXLang Value Parser - 值解析器

负责解析各种类型的值：
- 字面量：数字、字符串、布尔值、常量
- 代码块和列表
- 内联算术表达式
"""

from typing import List, Union, Optional
from .lexer import Token, TokenType
from ..ast_nodes import (
    ASTNode, LiteralNode, BlockNode, ListNode,
    IdentifierExpressionNode, InlineArithmeticNode
)


class ValueParserMixin:
    """值解析器 Mixin

    提供值解析相关的方法，设计为可被主 Parser 混入使用

    提供统一入口：
    - parse_value()  # 用于解析右值（rvalue）
    - parse_lvalue()  # 用于解析左值（lvalue）
    """

    # --------------- helpers ---------------
    def _parse_path_literal(self) -> LiteralNode:
        """内部：解析 path 字面量 IDENT(/IDENT)+ -> LiteralNode(path)"""
        parts = [self.advance().value]
        while self.check(TokenType.DIVIDE):
            self.advance()
            if self.check(TokenType.IDENTIFIER):
                parts.append(self.advance().value)
            else:
                current = self.peek()
                raise self.error(
                    "Expected identifier after '/' in path literal",
                    current,
                    expected="IDENTIFIER",
                    got=f"{current.type.name} '{current.value}'"
                )
        path = '/'.join(parts)
        node = LiteralNode(path, 'path')
        # line/column info will be set by caller if needed
        return node

    def _parse_constant_reference(self) -> LiteralNode:
        """内部：解析 @identifier 为常量字面量"""
        at_token = self.advance()
        # 内联算术 @[ expr ] - leave to caller (should have consumed LBRACKET already)
        if self.check(TokenType.LBRACKET):
            return self._parse_inline_arithmetic(at_token)
        if not self.check(TokenType.IDENTIFIER):
            raise self.error("Expected identifier after '@' in constant reference", self.peek())
        const_name = '@' + self.advance().value
        node = LiteralNode(const_name, 'constant')
        node.line = at_token.line
        node.column = at_token.column
        return node

    # --------------- public entry points ---------------
    def parse_value(self) -> ASTNode:
        """解析右值（value/rvalue）

        允许：numbers, strings, @constant, path, block/list, identifier-expr (calls, identifiers, macros)，color
        """
        # negative / numbers / strings / @ / blocks / paths
        if self.check(TokenType.MINUS) or self.check(TokenType.NUMBER) or self.check(TokenType.STRING) or self.check(TokenType.AT) or self.check(TokenType.LBRACE):
            # Use existing literal parser logic
            return self.parse_literal_value()
        
        if self.check(TokenType.IDENTIFIER) and self.peek().value in ['rgb', 'hsv']:
            return self.parse_literal_value()
        
        # color: rgb { r = 255 g = 0 b = 128 } 或 color { r = 255 g = 0 b = 128 }

        # path: IDENT / IDENT / ...
        if self.check(TokenType.IDENTIFIER) and self.peek_ahead(1) and self.peek_ahead(1).type == TokenType.DIVIDE:
            return self._parse_path_literal()

        # identifier-based expressions (calls, identifiers, macros)
        if self.check(TokenType.IDENTIFIER):
            return self.parse_identifier_expression()

        current = self.peek()
        raise self.error(
            "Unexpected token in value expression",
            current,
            expected="LBRACE, NUMBER, STRING, IDENTIFIER, or AT (@)",
            got=f"{current.type.name} '{current.value}'"
        )

    def parse_lvalue(self) -> ASTNode:
        """解析左值（lvalue）

        更严格，只允许 scope、scope.chain、identifier-expr、@identifier、数字（作为 key）和宏表达式。
        不允许 path、block 或 list。
        """
        # numeric keys are allowed (e.g., 0 = value handled earlier by caller)
        if self.check(TokenType.NUMBER):
            token = self.advance()
            node = LiteralNode(token.value)
            node.line = token.line
            node.column = token.column
            return node
        
        if self.check(TokenType.IDENTIFIER) and self.peek().value in ['rgb', 'hsv']:
            return self.parse_literal_value()

        # @constant allowed as lvalue
        if self.check(TokenType.AT):
            return self._parse_constant_reference()

        # path is not allowed on LHS
        if self.check(TokenType.IDENTIFIER) and self.peek_ahead(1) and self.peek_ahead(1).type == TokenType.DIVIDE:
            current = self.peek()
            raise self.error(
                "Path literal is not allowed on left-hand side",
                current,
                expected="identifier or scope",
                got="path literal"
            )

        # identifier-based LHS
        if self.check(TokenType.IDENTIFIER):
            return self.parse_identifier_expression()

        # strings as LHS handled elsewhere in parse_property_or_comparison
        current = self.peek()
        raise self.error(
            "Unexpected token in left-hand side of assignment",
            current,
            expected="IDENTIFIER, NUMBER, or @constant",
            got=f"{current.type.name} '{current.value}'"
        )

    # ---------------- Identifier expression parsing (moved from Parser) ----------------
    def parse_identifier_expression(self) -> ASTNode:
        """解析标识符表达式（直接在 ValueParserMixin 中实现）

        处理复杂的表达式结构，包括：
        - Scope 链: owner.overlord.capital_scope
        - 变量访问: owner.variable_name@prev
        - 特殊调用: value:tech_cost|AREA|, event_target:name
        - 路径: jobs/miners_add
        """
        # 保存当前位置
        start_pos = self.current_filtered

        # 收集表达式相关的 token（直到遇到非表达式 token）
        expr_tokens = []
        EXPRESSION_TOKENS = {
            TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING,
            TokenType.DOT, TokenType.COLON, TokenType.PIPE,
            TokenType.AT
        }  # NOTE: DIVIDE (path) handled by literal parser

        # NOTE: Path literal detection (IDENT '/' IDENT ...) is the caller's responsibility
        # (e.g., parse_value() or list parsing will handle it). Do not attempt to parse
        # path literals here to avoid duplicated logic and confusing control flow.

        last_token_type = None
        while not self.is_at_end():
            current = self.peek()

            # 遇到换行或非表达式 token，停止
            if current.type == TokenType.NEWLINE:
                break

            if current.type in EXPRESSION_TOKENS:
                # 检查连续标量（避免过度收集）
                if last_token_type in (TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING) and \
                   current.type in (TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING):
                    break

                expr_tokens.append(current)
                last_token_type = current.type
                self.advance()
            else:
                break

        if not expr_tokens:
            raise self.error("Expected identifier in expression")

        # 使用 ExpressionParser 解析（注入父级的错误工厂以保留上下文信息）
        from .expression_parser import ExpressionParser
        expr_parser = ExpressionParser(expr_tokens, self.context, error_fn=getattr(self, 'error', None))
        result = expr_parser.parse_expression()

        # 如果解析失败，抛出异常（不使用回退方案）
        if result is None:
            start_token = expr_tokens[0] if expr_tokens else self.peek()
            expr_str = ''.join(t.value for t in expr_tokens[:5])  # 显示前5个token
            if len(expr_tokens) > 5:
                expr_str += '...'
            raise self.error(
                f"Failed to parse expression: {expr_str}",
                start_token,
                expected="valid expression (scope chain, variable access, or special call)",
                got=f"unparseable token sequence"
            )

        return result

    # --------------- original literal parser (kept as helper) ---------------
    def parse_literal_value(self) -> ASTNode:
        # 负数值: -123 或 -$VAR$
        if self.check(TokenType.MINUS):
            minus_token = self.advance()
            # 递归解析后面的值
            inner_value = self.parse_literal_value()
            # 如果是 LiteralNode，将负号添加到值前面
            if isinstance(inner_value, LiteralNode):
                inner_value.value = '-' + str(inner_value.value)
                inner_value.line = minus_token.line
                inner_value.column = minus_token.column
                return inner_value
            # 如果是 IdentifierExpressionNode（如 -$VAR$），创建新的表达式
            elif isinstance(inner_value, IdentifierExpressionNode):
                inner_value.expression = '-' + inner_value.expression
                inner_value.line = minus_token.line
                inner_value.column = minus_token.column
                return inner_value
            else:
                # 其他情况，保持原样
                return inner_value
        
        # 代码块: { ... }
        if self.check(TokenType.LBRACE):
            return self.parse_block_or_list()
        
        # 数字
        if self.check(TokenType.NUMBER):
            token = self.advance()
            value = LiteralNode(token.value)
            value.line = token.line
            value.column = token.column
            return value
        
        # 字符串
        if self.check(TokenType.STRING):
            token = self.advance()
            value = LiteralNode(token.value, 'string')
            value.line = token.line
            value.column = token.column
            return value
        
        # 常量引用或内联算术: @constant 或 @[ expr ]
        if self.check(TokenType.AT):
            at_token = self.advance()
            
            # 检查是否是内联算术表达式 @[ expr ] 或 @\[ expr ]
            if self.check(TokenType.LBRACKET):
                return self._parse_inline_arithmetic(at_token)
            
            # 否则必须是 @identifier 形式的常量引用
            if not self.check(TokenType.IDENTIFIER):
                raise self.error("Expected identifier after '@' in constant reference", self.peek())
            
            const_name = '@' + self.advance().value
            value = LiteralNode(const_name, 'constant')
            value.line = at_token.line
            value.column = at_token.column
            return value
        
        # 路径字面量（jobs/miners_add）: Detect IDENTIFIER / IDENTIFIER / ... pattern
        # 优先识别 path（不需要引号），它应作为字面量处理
        if self.check(TokenType.IDENTIFIER) and self.peek_ahead(1) and self.peek_ahead(1).type == TokenType.DIVIDE:
            # 收集 parts separated by '/'
            parts = [self.advance().value]
            while self.check(TokenType.DIVIDE):
                self.advance()
                if self.check(TokenType.IDENTIFIER):
                    parts.append(self.advance().value)
                else:
                    # malformed path
                    current = self.peek()
                    raise self.error(
                        "Expected identifier after '/' in path literal",
                        current,
                        expected="IDENTIFIER",
                        got=f"{current.type.name} '{current.value}'"
                    )
            path = '/'.join(parts)
            node = LiteralNode(path, 'path')
            # Attempt to preserve line/column from first part
            node.line = start_token.line if (start_token := parts and None) else 0
            # Can't get accurate token line/column without tokens; leave 0, parser will set if needed
            return node

        #颜色: rgb { 255 0 128 } 或 hsv { 255 0 128 }
        if self.check(TokenType.IDENTIFIER) and self.peek().value in ['rgb', 'hsv']:
            color_type = self.advance().value  # rgb 或 hsv
            # 颜色值必须是一个块，里面有 r g b 或 h s v
            if not self.check(TokenType.LBRACE):
                self.error(
                    f"Expected '{{' after color type '{color_type}'",
                    self.peek(),
                    expected="LBRACE ({)",
                    got=f"{self.peek().type.name} '{self.peek().value}'"
                )
            list = self.parse_block_or_list()
            assert isinstance(list, ListNode)
            colors: List[int] = []
            for item in list.items:
                if isinstance(item, LiteralNode) and isinstance(item.value, (int, float)):
                    colors.append(int(item.value))
                else:
                    self.error(
                        f"Expected numeric color component in {color_type} color literal",
                        item,
                        expected="NUMBER",
                        got=f"{type(item).__name__}"
                    )
            color = LiteralNode.Color(color_type, colors)
            # 这里不强制要求块内必须有 r g b 或 h s v，留给后续验证
            node = LiteralNode(color)
            node.line = list.line
            node.column = list.column
            return node

        # 标识符（可能是布尔值、关键字、作用域链、特殊调用等）
        if self.check(TokenType.IDENTIFIER):
            return self.parse_identifier_expression()
        
        current = self.peek()
        raise self.error(
            f"Unexpected token in value expression",
            current,
            expected="LBRACE, NUMBER, STRING, IDENTIFIER, or AT (@)",
            got=f"{current.type.name} '{current.value}'"
        )
    
    def parse_block_or_list(self) -> Union[BlockNode, ListNode]:
        """解析代码块或列表
        
        代码块: { key = value ... }
        列表: { item1 item2 item3 }
        """
        start_token = self.peek()
        self.consume(TokenType.LBRACE, "Expected '{'")
        
        self.skip_newlines()  # 跳过开头的换行
        
        # 空块
        if self.check(TokenType.RBRACE):
            self.advance()
            return BlockNode([])
        
        # 判断是 Block 还是 List
        # 如果第一个 token 是逻辑运算符或条件参数，肯定是 Block
        if self.is_logic_operator() or self.check(TokenType.CONDITIONAL_PARAM):
            statements = []
            while not self.is_at_end() and not self.check(TokenType.RBRACE):
                self.skip_newlines()
                if self.check(TokenType.RBRACE):
                    break
                stmt = self.parse_statement()
                if stmt:
                    statements.append(stmt)
            
            self.consume(TokenType.RBRACE)
            block = BlockNode(statements)
            block.line = start_token.line
            block.column = start_token.column
            return block
        
        # 如果第一个 token 是 identifier、number 或 string，需要向前看找到 = 或比较运算符
        if self.check(TokenType.IDENTIFIER) or self.check(TokenType.NUMBER) or self.check(TokenType.STRING):
            # 向前扫描，跳过 . / 等，找到是否有 = 或比较运算符
            lookahead = 1
            has_assignment = False
            while lookahead < 20:  # 最多看 20 个 token
                ahead = self.peek_ahead(lookahead)
                if not ahead:
                    break
                
                # 跳过 NEWLINE
                if ahead.type == TokenType.NEWLINE:
                    lookahead += 1
                    continue
                
                # 找到赋值或比较运算符，这是 Block
                if ahead.type in (TokenType.EQUALS, TokenType.GT, TokenType.LT,
                                 TokenType.GTE, TokenType.LTE, TokenType.EQUALS_EQUALS,
                                 TokenType.NOT_EQUALS):
                    has_assignment = True
                    break
                
                # 如果遇到 }，说明是简单值列表
                if ahead.type == TokenType.RBRACE:
                    break
                
                # 继续向前看
                lookahead += 1
            
            if has_assignment:
                # 这是一个 Block
                statements = []
                while not self.is_at_end() and not self.check(TokenType.RBRACE):
                    self.skip_newlines()
                    if self.check(TokenType.RBRACE):
                        break
                    stmt = self.parse_statement()
                    if stmt:
                        statements.append(stmt)
                
                self.consume(TokenType.RBRACE)
                block = BlockNode(statements)
                block.line = start_token.line
                block.column = start_token.column
                return block
        
        # 否则是 List（值列表）
        items = []
        
        while not self.is_at_end() and not self.check(TokenType.RBRACE):
            self.skip_newlines()
            if self.check(TokenType.RBRACE):
                break

            # 解析列表项：统一交给 parse_value() 处理各种值类型（数字/字符串/路径/标识符/调用/@常量/块等）
            # 保留对孤立 '@' 的向后兼容：如果后面没有 IDENT 或 LBRACKET，视为字符串 '@'
            if self.check(TokenType.AT) and not (self.peek_ahead(1) and self.peek_ahead(1).type in (TokenType.IDENTIFIER, TokenType.LBRACKET)):
                # 单独的 @，向后兼容地当作标识符文字
                self.advance()
                items.append(LiteralNode('@', 'identifier'))
                continue

            # 如果可以作为值的起始 token，则委托 parse_value()
            if self.check(TokenType.NUMBER) or self.check(TokenType.STRING) or self.check(TokenType.IDENTIFIER) or self.check(TokenType.AT) or self.check(TokenType.MINUS) or self.check(TokenType.LBRACE):
                value_node = self.parse_value()
                items.append(value_node)
                continue

            # 其他情况退出
            break
        
        self.consume(TokenType.RBRACE)
        list_node = ListNode(items)
        list_node.line = start_token.line
        list_node.column = start_token.column
        return list_node
    
    def _parse_inline_arithmetic(self, at_token: Token) -> ASTNode:
        r"""解析内联算术表达式
        
        格式: @[ expr ] 或 @\[ expr ]
        例如: @[( 72 * $PROGRESS$ )]
        
        当前实现：保存原始表达式文本，不解析内部结构
        """
        # 检查是否是转义形式 @\[
        escaped = at_token.value == '@\\'
        
        # 消费 [
        self.consume(TokenType.LBRACKET, "Expected '[' after '@' in inline arithmetic")
        
        # 收集所有 token 直到匹配的 ]
        expression_tokens = []
        bracket_depth = 1  # 已经消费了一个 [
        
        while not self.is_at_end() and bracket_depth > 0:
            current = self.peek()
            
            if current.type == TokenType.LBRACKET:
                bracket_depth += 1
            elif current.type == TokenType.RBRACKET:
                bracket_depth -= 1
                if bracket_depth == 0:
                    # 找到匹配的右括号，不包含在表达式中
                    break
            
            expression_tokens.append(self.advance())
        
        # 消费结束的 ]
        if not self.check(TokenType.RBRACKET):
            current = self.peek()
            raise self.error(
                "Expected ']' to close inline arithmetic expression",
                current,
                expected="RBRACKET (])",
                got=f"{current.type.name if current else 'EOF'}"
            )
        self.advance()
        
        # 构建表达式文本（不添加空格以保留原始格式）
        expression = ''.join(token.value for token in expression_tokens)
        
        # 创建节点
        node = InlineArithmeticNode(expression, escaped)
        node.line = at_token.line
        node.column = at_token.column
        return node
