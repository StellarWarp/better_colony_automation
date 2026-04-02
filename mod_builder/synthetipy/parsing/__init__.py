"""
PDXLang Parsing Module - 解析模块

统一的解析模块，包含：
- Lexer: 词法分析器
- Parser: 语法分析器
- ExpressionParser: 表达式解析器
- ParserContext: 解析上下文
"""

from .lexer import Lexer, Token, TokenType, lex
from .parser_context import ParserContext, get_parser_context
from .expression_parser import ExpressionParser
from .parser_utils import ParserError

# Note: Parser is imported from parent module to avoid circular import
# Use: from synthetipy import Parser

__all__ = [
    # Lexer
    'Lexer',
    'Token',
    'TokenType',
    'lex',
    
    # Context
    'ParserContext',
    'get_parser_context',
    
    # Expression Parser
    'ExpressionParser',
    
    # Errors
    'ParserError',
]
