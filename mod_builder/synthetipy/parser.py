"""
PDXLang Patcher - 语法分析器（重构版）
将 Token 流转换为抽象语法树 (AST)

重构说明：
- 主 Parser 类作为协调器，委托给各个专门的 mixin
- ParserContextHelper 处理错误和上下文
- StatementParserMixin 处理语句解析
- ValueParserMixin 处理值解析
- ExpressionParser 处理表达式解析
"""

from pathlib import Path
from typing import List, Optional, Union
from .parsing.lexer import Token, TokenType
from .parsing.parser_context import ParserContext, get_parser_context
from .parsing.expression_parser import ExpressionParser
from .parsing.parser_utils import ParserError, ParserContextHelper
from .parsing.statement_parser import StatementParserMixin
from .parsing.value_parser import ValueParserMixin
from .ast_nodes import *
from .parsing.lexer import Lexer

class Parser(StatementParserMixin, ValueParserMixin):
    """递归下降语法分析器（重构版）
    
    使用 Mixin 模式将功能分散到各个模块：
    - StatementParserMixin: 语句解析
    - ValueParserMixin: 值解析
    - ExpressionParser: 表达式解析（独立类）
    """
    
    def __init__(self, tokens: List[Token], source_text: str = None, context: ParserContext = None):
        self.tokens = tokens
        self.current = 0
        self.source_text = source_text
        
        # 只过滤掉注释和 EOF，保留 NEWLINE 用于判断表达式边界
        self.filtered_tokens = [
            t for t in tokens 
            if t.type not in (TokenType.COMMENT, TokenType.EOF)
        ]
        self.current_filtered = 0
        
        # 解析器上下文（游戏规则）
        self.context = context if context else get_parser_context()
        
        # 上下文辅助器（错误处理）
        self.context_helper = ParserContextHelper(source_text, self.filtered_tokens)
    
    # ==================== 辅助方法 ====================
    
    def is_at_end(self) -> bool:
        """是否到达末尾"""
        return self.current_filtered >= len(self.filtered_tokens)
    
    def peek(self) -> Optional[Token]:
        """查看当前 token"""
        if self.is_at_end():
            return None
        return self.filtered_tokens[self.current_filtered]
    
    def peek_ahead(self, offset: int = 1) -> Optional[Token]:
        """向前查看 token"""
        pos = self.current_filtered + offset
        if pos >= len(self.filtered_tokens):
            return None
        return self.filtered_tokens[pos]
    
    def previous(self) -> Optional[Token]:
        """获取前一个 token"""
        if self.current_filtered == 0:
            return None
        return self.filtered_tokens[self.current_filtered - 1]
    
    def advance(self) -> Token:
        """前进并返回当前 token"""
        if not self.is_at_end():
            token = self.filtered_tokens[self.current_filtered]
            self.current_filtered += 1
            return token
        return self.previous()
    
    def check(self, token_type: TokenType) -> bool:
        """检查当前 token 类型"""
        if self.is_at_end():
            return False
        return self.peek().type == token_type
    
    def check_value(self, value: str) -> bool:
        """检查当前 token 的值"""
        if self.is_at_end():
            return False
        return self.peek().value == value
    
    def match(self, *types: TokenType) -> bool:
        """匹配多个 token 类型之一"""
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False
    
    def consume(self, token_type: TokenType, message: str = None) -> Token:
        """消费指定类型的 token"""
        if self.check(token_type):
            return self.advance()
        
        current = self.peek()
        if message is None:
            message = "Token mismatch"
        
        expected_name = token_type.name
        got_name = current.type.name if current else "EOF"
        got_value = f"'{current.value}'" if current else "end of file"
        
        raise self.error(
            message,
            current,
            expected=expected_name,
            got=f"{got_name} {got_value}"
        )
    
    def is_logic_operator(self) -> bool:
        """检查是否是逻辑运算符"""
        if self.is_at_end():
            return False
        return self.peek().type in (
            TokenType.OR, TokenType.AND, TokenType.NOT,
            TokenType.NAND, TokenType.NOR
        )
    
    def skip_newlines(self):
        """跳过所有连续的 NEWLINE token"""
        while not self.is_at_end() and self.check(TokenType.NEWLINE):
            self.advance()
    
    def error(self, message: str, token: Optional[Token] = None, 
              expected: str = None, got: str = None) -> ParserError:
        """创建格式化的解析错误（委托给 context_helper）"""
        return self.context_helper.create_error(message, token, expected, got)
    
    # ==================== 主解析方法 ====================
    
    def parse(self) -> DocumentNode:
        """解析整个文档"""
        statements = []
        max_iterations = 100000  # 防止死循环
        iterations = 0
        
        while not self.is_at_end():
            self.skip_newlines()  # 跳过空行
            if self.is_at_end():
                break
            
            iterations += 1
            if iterations > max_iterations:
                raise self.error("Reached maximum iterations - possible infinite loop")
            
            stmt = self.parse_top_level_statement()
            if stmt:
                statements.append(stmt)
        
        return DocumentNode(statements)
    
    def parse_top_level_statement(self) -> Optional[ASTNode]:
        """解析顶层语句（对象定义或常量定义）"""
        if self.is_at_end():
            return None
        
        # 常量定义：@constant = value
        if self.check(TokenType.AT):
            at_token = self.advance()
            
            # @ 后面必须是标识符
            if not self.check(TokenType.IDENTIFIER):
                raise self.error(
                    "Expected identifier after '@' in constant definition",
                    expected="IDENTIFIER",
                    got=f"{self.peek().type.name} '{self.peek().value}'"
                )
            
            const_name_token = self.advance()
            const_name = '@' + const_name_token.value  # 例如 "@buildings_t1"
            
            # 必须有 =
            self.consume(TokenType.EQUALS, f"Expected '=' after constant '{const_name}'")
            
            # 解析值（通常是数字或标识符）
            value = self.parse_value()
            
            # 创建常量定义节点
            const_def = ConstantDefinitionNode(const_name, value)
            const_def.line = at_token.line
            const_def.column = at_token.column
            
            return const_def
        
        # 对象定义格式: identifier/number/string = { ... }
        if self.check(TokenType.IDENTIFIER) or self.check(TokenType.NUMBER) or self.check(TokenType.STRING):
            # 保存位置，以便回退
            saved_pos = self.current_filtered
            name_token = self.peek()
            
            # 尝试使用统一的解析方法
            try:
                result = self.parse_property_or_comparison()
                
                # 检查是否是对象定义（key = { ... }）
                if isinstance(result, PropertyNode) and isinstance(result.value, BlockNode):
                    # 这是对象定义，转换为 ObjectNode
                    obj = ObjectNode(result.key, result.value)
                    obj.line = result.line
                    obj.column = result.column
                    return obj
                else:
                    # 这是普通的属性或比较（虽然在顶层不常见）
                    return result
            except ParserError:
                # 如果解析失败，回退并抛出错误
                self.current_filtered = saved_pos
                raise
        
        # 无法识别的顶层语句
        current = self.peek()
        raise self.error(
            f"Unexpected token at top level",
            current,
            expected="IDENTIFIER or AT (@)",
            got=f"{current.type.name} '{current.value}'"
        )
    
    def parse_block(self) -> BlockNode:
        """解析代码块 { ... }"""
        self.consume(TokenType.LBRACE, "Expected '{'")
        
        statements = []
        
        while not self.is_at_end() and not self.check(TokenType.RBRACE):
            self.skip_newlines()  # 跳过空行
            if self.check(TokenType.RBRACE):
                break
            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
        
        self.consume(TokenType.RBRACE, "Expected '}'")
        
        return BlockNode(statements)


def parse(text: str) -> DocumentNode:

    
    lexer = Lexer(text)
    tokens = lexer.tokenize()
    
    parser = Parser(tokens, source_text=text)
    return parser.parse()

def parse_file(file_path: Path) -> DocumentNode:
    """便捷函数：直接从文件解析为 AST"""
    with file_path.open("r", encoding="utf-8") as f:
        text = f.read()
    return parse(text)
