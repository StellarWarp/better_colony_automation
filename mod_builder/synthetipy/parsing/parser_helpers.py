"""
PDXLang Parser Helpers - 解析器通用辅助方法

提供 Parser 和 ExpressionParser 共用的辅助方法，避免代码重复
"""

from typing import Optional, List
from .lexer import Token, TokenType


class TokenStreamMixin:
    """Token 流操作 Mixin
    
    提供通用的 token 遍历和检查方法
    
    要求使用者具有以下属性：
    - tokens: List[Token] - token 列表
    - current: int - 当前位置索引
    """
    
    def is_at_end(self) -> bool:
        """是否到达末尾"""
        return self.current >= len(self.tokens)
    
    def peek(self) -> Optional[Token]:
        """查看当前 token"""
        if self.is_at_end():
            return None
        return self.tokens[self.current]
    
    def peek_ahead(self, offset: int = 1) -> Optional[Token]:
        """向前查看 token"""
        pos = self.current + offset
        if pos >= len(self.tokens):
            return None
        return self.tokens[pos]
    
    def previous(self) -> Optional[Token]:
        """获取前一个 token"""
        if self.current == 0:
            return None
        return self.tokens[self.current - 1]
    
    def advance(self) -> Token:
        """前进并返回当前 token"""
        if not self.is_at_end():
            token = self.tokens[self.current]
            self.current += 1
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

    def error(self, message: str, token: Optional[Token] = None, expected: str = None, got: str = None):
        """创建一个简化的 ParserError（供 ExpressionParser 使用）"""
        from .parser_utils import ParserError
        if expected and got:
            message = f"{message}: expected {expected}, got {got}"
        elif expected:
            message = f"{message}: expected {expected}"
        return ParserError(message, token) 
