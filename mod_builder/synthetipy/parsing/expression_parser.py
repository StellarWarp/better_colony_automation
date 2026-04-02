"""
PDXLang Expression Parser - 表达式解析

遵循正确的 PDX 语法规则：

表达式形式: [scope(optional)].[identifier/call]

语法规则：
1. event_target:identifier -> ScopeNode (不是调用!)
2. value:/trigger:/modifier: -> SpecialCallNode (真正的调用)
3. identifier@scope_binding -> VariableAccessNode with binding
4. owner.overlord.capital_scope -> ScopeNode
5. scope 可以作为独立左值: owner = { ... }

Examples:
  - event_target:federation_leader -> ScopeNode
  - value:tech_cost|AREA| -> SpecialCallNode  
  - owner.capital_scope -> ScopeNode
  - variable_name@prev -> VariableAccessNode with scope_binding
  - owner.trigger:is_valid -> ScopeNode + SpecialCallNode
"""

from typing import Optional, List, Tuple, Any
from ..ast_nodes import (
    ASTNode, LiteralNode, IdentifierExpressionNode,
    IdentifierNode as IdNode, ScopeObjectNode, EventTargetNode, ScopeNode,
    CallInfo, MacroExpression
)
from .lexer import Token, TokenType
from .parser_context import ParserContext
from .parser_utils import ParserError
from .parser_helpers import TokenStreamMixin


# 真正的调用前缀（不是 event_target!）
CALL_PREFIXES = {'value', 'trigger', 'modifier'}

# Event target 前缀（是 Scope，不是调用）
EVENT_TARGET_PREFIX = 'event_target'


class ExpressionParser(TokenStreamMixin):
    """表达式解析器
    
    继承 TokenStreamMixin 获得通用 token 操作方法

    支持注入错误工厂（error_fn），通常传入 Parser.error 以获得完整上下文信息。
    """
    
    def __init__(self, tokens: List[Token], context: ParserContext, error_fn=None):
        self.tokens = tokens
        self.current = 0
        self.context = context
        # 错误工厂：函数签名 (message, token, expected, got) -> ParserError
        self._error_fn = error_fn

    def _raise_error(self, message: str, token: Optional[Token] = None, expected: str = None, got: str = None):
        """创建并抛出错误，优先使用注入的 error_fn，否则回退到本地简单实现"""
        if self._error_fn:
            raise self._error_fn(message, token, expected, got)
        # 回退：使用本地 ParserError（较少上下文）
        from .parser_utils import ParserError
        if expected and got:
            message = f"{message}: expected {expected}, got {got}"
        elif expected:
            message = f"{message}: expected {expected}"
        raise ParserError(message, token)
    
    # ==================== 表达式解析 ====================
    
    def parse_expression(self) -> ASTNode:
        """解析完整表达式（入口点）
        
        语法结构（递归分析）：
            expression = [scope].[identifier/call] | [identifier/call]

        解析流程：
            1. 检查是否以 scope 开始
            2. 如果是 scope，解析 scope（可能是 scope chain）
            3. 检查是否有 . 后跟 identifier/call
            4. 如果没有 scope，直接解析 identifier/call
        """
        # 注意：字面量（数字、字符串、path、@constant、负数）由主 Parser 的 LiteralValueParserMixin 处理
        # ExpressionParser 主要处理以 IDENTIFIER 开始的结构化表达式，但保留对 path 的回退处理
        if self.check(TokenType.IDENTIFIER):
            start_token = self.peek()
            identifier = self.peek().value

            # Pre-scan the upcoming expression tokens to decide macro handling
            expr_tokens = []
            i = 0
            EXPR_TOKS = {
                TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING,
                TokenType.DOT, TokenType.COLON, TokenType.PIPE, TokenType.AT
            }
            while True:
                t = self.peek_ahead(i)
                if not t or t.type == TokenType.NEWLINE:
                    break
                if t.type in EXPR_TOKS:
                    expr_tokens.append(t)
                    i += 1
                    continue
                break

            # If expression contains any macro-like identifier, decide whether
            # to treat whole expression as MacroExpression or allow structured parse.
            has_macro = any(t.type == TokenType.IDENTIFIER and '$' in t.value for t in expr_tokens)

            # Exception 1: event_target:$MACRO$ should remain structured,
            # but only when the macro identifier is directly after ':' and is followed by '.' or nothing.
            is_event_target_macro = False
            if len(expr_tokens) >= 3 and expr_tokens[0].type == TokenType.IDENTIFIER and expr_tokens[0].value == EVENT_TARGET_PREFIX and expr_tokens[1].type == TokenType.COLON:
                third = expr_tokens[2]
                if third.type == TokenType.IDENTIFIER and third.value.startswith('$') and third.value.endswith('$'):
                    # allow only if there's no token after it or the next token is DOT (scope continuation)
                    if len(expr_tokens) == 3 or (len(expr_tokens) > 3 and expr_tokens[3].type == TokenType.DOT):
                        is_event_target_macro = True

            # Exception 2: calls starting with known CALL_PREFIXES are allowed to be parsed
            # only if any macros present are pure macro parameter values (value token starts/ends with $)
            # and the macro token is *in a parameter value position* (surrounded by PIPE on both sides).
            def _is_call_with_pure_macro_params(tokens: List[Token]) -> bool:
                if not (len(tokens) >= 2 and tokens[0].type == TokenType.IDENTIFIER and tokens[0].value in CALL_PREFIXES and tokens[1].type == TokenType.COLON):
                    return False

                # If there are no macro-looking identifiers, accept (no special macro handling)
                has_macro = any(t.type == TokenType.IDENTIFIER and '$' in t.value for t in tokens)
                if not has_macro:
                    return True

                # For each identifier token that contains '$', ensure it is a pure macro
                # and that it is surrounded by PIPE tokens (| name | $MACRO$ |)
                for i, t in enumerate(tokens):
                    if t.type == TokenType.IDENTIFIER and '$' in t.value:
                        if not (t.value.startswith('$') and t.value.endswith('$')):
                            return False
                        prev_tok = tokens[i - 1] if i - 1 >= 0 else None
                        next_tok = tokens[i + 1] if i + 1 < len(tokens) else None
                        if not (prev_tok and prev_tok.type == TokenType.PIPE and next_tok and next_tok.type == TokenType.PIPE):
                            return False
                return True

            is_call_prefix = _is_call_with_pure_macro_params(expr_tokens)

            if has_macro and not (is_event_target_macro or is_call_prefix):
                # Treat whole expression as MacroExpression
                raw = ''.join(t.value for t in expr_tokens)
                node = IdentifierExpressionNode()
                node.macro_expression = MacroExpression(raw)
                node.line = start_token.line
                node.column = start_token.column
                return node

            # Do not fallback to parsing path literals here. Path literals should
            # be handled by the ValueParser (parse_value()). If we see a DIVIDE here,
            # that's an error in expression context.
            if self.peek_ahead(1) and self.peek_ahead(1).type == TokenType.DIVIDE:
                current = self.peek_ahead(1)
                self._raise_error(
                    "Path literal encountered in expression context",
                    current,
                    expected="identifier or scope",
                    got="path literal"
                )

            # 检查是否是 scope（包括 event_target:）
            if self._is_scope_start():
                scope = self.parse_scope()
                
                # scope 后面可以跟 . identifier/call
                if self.check(TokenType.DOT):
                    self.advance()  # 跳过 .
                    return self.parse_identifier_or_call(scope)
                else:
                    # 独立的 scope 作为左值
                    return scope
            else:
                # 不是 scope，直接解析 identifier/call
                return self.parse_identifier_or_call(None)
        
        # 其他情况（块、列表等）交给主 parser
        return None
    
    def _is_scope_start(self) -> bool:
        """检查当前位置是否是 scope 的开始"""
        if not self.check(TokenType.IDENTIFIER):
            return False
        
        identifier = self.peek().value
        
        # event_target: 是 scope
        if identifier == EVENT_TARGET_PREFIX:
            next_token = self.peek_ahead(1)
            return next_token and next_token.type == TokenType.COLON
        
        # 已知的 scope 名称
        if self.context.is_scope(identifier):
            return True
        
        return False
    

    
    
    def parse_scope(self) -> ScopeNode:
        """解析 scope 或 scope chain
        
        语法：
            scope = single_scope ( '.' single_scope )*
            single_scope = 'event_target' ':' identifier | scope_identifier
        
        解析流程：
            while node is scope:
                add to scope chain
        """
        scopes = []
        
        # 解析第一个 scope
        first_scope = self.parse_single_scope()
        if first_scope is None:
            return None
        scopes.append(first_scope)
        
        # 继续解析 scope chain
        while self.check(TokenType.DOT):
            # 向前看：下一个是否还是 scope
            next_pos = self.current + 1
            if next_pos >= len(self.tokens):
                break
            
            # 保存位置以便回退
            saved_pos = self.current
            self.advance()  # 跳过 .
            
            # 尝试解析下一个 scope
            if self._is_scope_start():
                next_scope = self.parse_single_scope()
                if next_scope:
                    scopes.append(next_scope)
                else:
                    # 解析失败，回退
                    self.current = saved_pos
                    break
            else:
                # 不是 scope，回退
                self.current = saved_pos
                break
        
        return ScopeNode(scopes)
    
    def parse_single_scope(self) -> Optional[ScopeObjectNode]:
        """解析单个 scope
        
        可能是：
        - event_target:[identifier]  <- 递归调用 identifier 解析
        - 已知的 scope 名称（owner, planet, etc.）
        """
        if not self.check(TokenType.IDENTIFIER):
            return None
        
        start_token = self.peek()
        identifier = self.advance().value
        
        # event_target:[identifier] - 解析为 EventTargetNode(target=IdentifierNode(...))
        if identifier == EVENT_TARGET_PREFIX and self.check(TokenType.COLON):
            self.advance()  # 跳过 :

            if not self.check(TokenType.IDENTIFIER):
                current = self.peek()
                self._raise_error(
                    "Expected identifier after 'event_target:'",
                    start_token,
                    expected="IDENTIFIER",
                    got=f"{current.type.name} '{current.value}'"
                )

            target_name = self.advance().value

            # 创建 IdentifierNode 作为 target
            target = IdNode(target_name)

            # 如果 target 是纯宏（$NAME$），保存为 MacroParam 以供后续使用
            if target_name.startswith('$') and target_name.endswith('$'):
                inner = target_name[1:-1]
                from ..ast_nodes_expression import MacroParam
                node = EventTargetNode(target)
                node.target_macro = MacroParam(inner)
            else:
                node = EventTargetNode(target)

            node.line = start_token.line
            node.column = start_token.column
            return node
        
        # 已知的 scope 名称 -> 返回单个 ScopeObjectNode，链式组合由 parse_scope 处理
        if self.context.is_scope(identifier):
            node = ScopeObjectNode(identifier)
            node.line = start_token.line
            node.column = start_token.column
            return node
        
        # 不是 scope，回退
        self.current -= 1
        return None
    
    def parse_identifier_or_call(self, scope: Optional[ASTNode] = None) -> ASTNode:
        """解析 identifier 或 call
        
        语法：
            identifier_or_call = call | identifier
            call = call_prefix ':' function_name ( '|' args )*
            identifier = name ( '@' scope_binding )?
        
        Args:
            scope: 可选的前置 scope（来自 scope.identifier/call）
        """
        if not self.check(TokenType.IDENTIFIER):
            return None
        
        start_token = self.peek()
        identifier = self.advance().value
        
        # Macro-mixed expressions: if identifier contains '$', treat as macro expression
        if '$' in identifier:
            macro = MacroExpression(identifier)
            node = IdentifierExpressionNode()
            node.macro_expression = macro
            node.line = start_token.line
            node.column = start_token.column
            return node

        # 检查是否是 call（value:/trigger:/modifier:）
        if identifier in CALL_PREFIXES and self.check(TokenType.COLON):
            return self.parse_call(identifier, start_token, scope)

        # 否则是普通 identifier
        return self.parse_identifier(identifier, start_token, scope)
    
    def parse_call(self, call_type: str, start_token: Token, scope: Optional[ASTNode] = None) -> IdentifierExpressionNode:
        """解析特殊调用并返回 IdentifierExpressionNode 包含 CallInfo

        格式：value:function_name|key|value|...
        返回：IdentifierExpressionNode(call_info=CallInfo(...), scope=scope)
        """
        self.advance()  # 跳过 :

        # 读取函数名
        if not self.check(TokenType.IDENTIFIER):
            current = self.peek()
            self._raise_error(
                f"Expected function name after '{call_type}:'",
                start_token,
                expected="IDENTIFIER",
                got=f"{current.type.name} '{current.value}'"
            )

        function_name = self.advance().value

        # 解析参数（键值对）
        arguments: List[Tuple[str, Any]] = []
        if self.check(TokenType.PIPE):
            arguments = self.parse_pipe_arguments()

        call_info = CallInfo(call_type, function_name, arguments)

        node = IdentifierExpressionNode()
        node.call_info = call_info
        if scope:
            if isinstance(scope, ScopeNode):
                node.scope = scope
            else:
                # single scope object (ScopeObjectNode or EventTargetNode)
                node.scope = ScopeNode([scope]) if not isinstance(scope, ScopeNode) else scope

        node.line = start_token.line
        node.column = start_token.column
        return node
    
    def parse_identifier(self, name: str, start_token: Token, scope: Optional[ASTNode] = None) -> IdentifierExpressionNode:
        """解析 identifier

        格式：name@[scope_binding]
        scope_binding 使用递归解析为 ScopeNode
        
        Args:
            name: 标识符名称
            start_token: 起始 token
            scope: 可选的前置 scope
        """
        # 解析 scope binding（@[scope]）: 支持复杂 scope
        scope_binding_node: Optional[ScopeNode] = None
        if self.check(TokenType.AT):
            self.advance()  # 跳过 @
            # If next is scope-like, try parsing as scope
            if self.check(TokenType.IDENTIFIER):
                # If there's a dot or colon ahead, parse a full scope; else single scope object
                if self.peek_ahead(1) and self.peek_ahead(1).type in (TokenType.DOT, TokenType.COLON):
                    # attempt to parse a scope starting here
                    scope_binding_node = self.parse_scope()
                else:
                    single_name = self.advance().value
                    scope_binding_node = ScopeNode([ScopeObjectNode(single_name)])

        # 布尔字面量
        if name.lower() in ('yes', 'no', 'true', 'false'):
            node = LiteralNode(name)
            node.line = start_token.line
            node.column = start_token.column
            return node

        # 构建 identifier 节点
        identifier_node = IdNode(name, scope_binding=scope_binding_node)

        # 如果有前置 scope，创建 IdentifierExpressionNode(scope + identifier)
        if scope:
            expr = IdentifierExpressionNode()
            # scope may be a single scope object or ScopeNode
            if isinstance(scope, ScopeNode):
                expr.scope = scope
            else:
                expr.scope = ScopeNode([scope])
            expr.identifier = identifier_node
            expr.line = start_token.line
            expr.column = start_token.column
            return expr

        # 没有前置 scope：独立的 IdentifierExpressionNode
        expr = IdentifierExpressionNode()
        expr.identifier = identifier_node
        expr.line = start_token.line
        expr.column = start_token.column
        return expr
    
    def parse_pipe_arguments(self) -> List[ASTNode]:
        """解析管道参数（成对参数）
        
        格式: |param_name_1|param_value_1|param_name_2|param_value_2|
        参数是成对出现的：名称-值对
        
        注意：
        - 如果参数名后面没有对应的值，报错
        - 最后一个 | 是结束标记（后面没有参数）
        """
        arguments = []
        
        while self.check(TokenType.PIPE):
            self.advance()  # 跳过 |
            
            # 检查是否结束（没有更多参数）
            if self.is_at_end():
                break
            
                # 读取参数名
            if self.check(TokenType.IDENTIFIER):
                param_name = self.advance().value
            elif self.check(TokenType.NUMBER):
                param_name = self.advance().value
            elif self.check(TokenType.STRING):
                param_name = self.advance().value
            else:
                # 没有参数名，说明是最后一个 | 或遇到其他 token，参数列表结束
                break

            # 参数名后面必须有 |
            if not self.check(TokenType.PIPE):
                current = self.peek()
                self._raise_error(
                    f"Expected '|' after parameter name '{param_name}' in scripted value call",
                    current,
                    expected="PIPE (|)",
                    got=f"{current.type.name} '{current.value}'"
                )

            self.advance()  # 跳过 |

            # 读取参数值（必需），并将其转换为合适的类型（MacroExpression or raw value）
            if self.check(TokenType.IDENTIFIER):
                val = self.advance().value
                # If the value is a pure macro like $PARAM$ or $PARAM|default$, store MacroParam
                if val.startswith('$') and val.endswith('$'):
                    inner = val[1:-1]
                    from ..ast_nodes_expression import MacroParam
                    arguments.append((param_name, MacroParam(inner)))
                elif '$' in val:
                    # Mixed macros in parameter values should have been handled at expression entry
                    current = self.previous()
                    self._raise_error(
                        f"Mixed macro '{val}' encountered in parameter value; expected pure macro or raw value",
                        current,
                        expected="IDENTIFIER or pure macro ($NAME$)",
                        got=f"IDENTIFIER '{val}'"
                    )
                else:
                    arguments.append((param_name, val))
            elif self.check(TokenType.NUMBER):
                val = self.advance().value
                arguments.append((param_name, val))
            elif self.check(TokenType.STRING):
                val = self.advance().value
                arguments.append((param_name, val))
            else:
                # 参数名后面没有值
                current = self.peek()
                self._raise_error(
                    f"Expected parameter value after '{param_name}|' in scripted value call",
                    current,
                    expected="IDENTIFIER, NUMBER, or STRING",
                    got=f"{current.type.name} '{current.value}'"
                )
        
        return arguments
    
    
    def parse_path_expression(self, first_part: str, start_token: Token) -> ASTNode:
        """旧方法，path 现在由字面量解析器处理。保留以防意外调用，但将其视为字面量。"""
        parts = [first_part]
        while self.check(TokenType.DIVIDE):
            self.advance()
            if self.check(TokenType.IDENTIFIER):
                parts.append(self.advance().value)
            else:
                break
        path = '/'.join(parts)
        node = LiteralNode(path, 'path')
        node.line = start_token.line
        node.column = start_token.column
        return node
