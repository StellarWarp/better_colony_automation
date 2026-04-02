"""
PDXLang Patcher - 简化的词法分析器实现（MVP）
用于演示核心概念
"""

import re
from typing import List, Optional, Tuple
from enum import Enum, auto


class TokenType(Enum):
    """Token 类型枚举"""
    # 字面量
    IDENTIFIER = auto()      # building_research_lab_1
    NUMBER = auto()          # 100, 3.14
    STRING = auto()          # "some text"
    
    # 运算符和符号
    EQUALS = auto()          # =
    LBRACE = auto()          # {
    RBRACE = auto()          # }
    LBRACKET = auto()        # [
    RBRACKET = auto()        # ]
    GT = auto()              # >
    LT = auto()              # <
    GTE = auto()             # >=
    LTE = auto()             # <=
    EQUALS_EQUALS = auto()   # ==
    NOT_EQUALS = auto()      # !=
    PIPE = auto()            # |
    DOT = auto()             # .
    COLON = auto()           # :
    AT = auto()              # @
    
    # 算术运算符
    PLUS = auto()            # +
    MINUS = auto()           # -
    MULTIPLY = auto()        # *
    DIVIDE = auto()          # /
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    
    # 逻辑运算符
    OR = auto()              # OR
    AND = auto()             # AND
    NOT = auto()             # NOT
    NAND = auto()            # NAND
    NOR = auto()             # NOR
    
    # 特殊
    CONSTANT = auto()        # @b1_time (编译时常量)
    CONDITIONAL_PARAM = auto()  # [[PARAM]
    COMMENT = auto()         # # comment
    NEWLINE = auto()         # \n
    EOF = auto()             # 文件结束


class Token:
    """词法单元"""
    
    def __init__(
        self,
        type: TokenType,
        value: str,
        line: int,
        column: int,
        whitespace_before: str = '',
        comment_after: str = ''
    ):
        self.type = type
        self.value = value
        self.line = line
        self.column = column
        self.whitespace_before = whitespace_before  # 保留前置空白
        self.comment_after = comment_after          # 保留行尾注释
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column})"
    
    def __str__(self):
        return self.value


class Lexer:
    """词法分析器"""
    
    # 关键字（逻辑运算符）
    KEYWORDS = {
        'OR': TokenType.OR,
        'AND': TokenType.AND,
        'NOT': TokenType.NOT,
        'NAND': TokenType.NAND,
        'NOR': TokenType.NOR,
    }
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
    
    def current_char(self) -> Optional[str]:
        """获取当前字符"""
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]
    
    def peek_char(self, offset: int = 1) -> Optional[str]:
        """向前查看字符"""
        pos = self.pos + offset
        if pos >= len(self.text):
            return None
        return self.text[pos]
    
    def advance(self):
        """前进一个字符"""
        if self.pos < len(self.text):
            if self.text[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
    
    def skip_whitespace(self) -> str:
        """跳过空白字符并返回跳过的内容"""
        whitespace = ''
        while self.current_char() and self.current_char() in ' \t\r':
            whitespace += self.current_char()
            self.advance()
        return whitespace
    
    def read_comment(self) -> str:
        """读取注释"""
        comment = ''
        if self.current_char() == '#':
            while self.current_char() and self.current_char() != '\n':
                comment += self.current_char()
                self.advance()
        return comment
    
    def read_string(self) -> str:
        """读取字符串字面量"""
        quote = self.current_char()
        self.advance()  # 跳过开始引号
        
        result = ''
        while self.current_char() and self.current_char() != quote:
            if self.current_char() == '\\':
                self.advance()
                # 处理转义字符
                escape_char = self.current_char()
                if escape_char == 'n':
                    result += '\n'
                elif escape_char == 't':
                    result += '\t'
                elif escape_char == '\\':
                    result += '\\'
                elif escape_char == quote:
                    result += quote
                else:
                    result += escape_char
                self.advance()
            else:
                result += self.current_char()
                self.advance()
        
        self.advance()  # 跳过结束引号
        return result
    
    def read_number(self) -> Tuple[str, TokenType]:
        """读取数字
        
        如果数字后面紧跟字母或标识符字符，则作为标识符处理
        例如: 6monthsocietycost 是一个标识符，不是数字
        """
        num_str = ''
        has_dot = False
        
        # 处理负号
        if self.current_char() == '-':
            num_str += self.current_char()
            self.advance()
        
        while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
            if self.current_char() == '.':
                if has_dot:
                    break  # 第二个点，停止
                # 只有当点后面是数字时才作为小数点
                if not (self.peek_char() and self.peek_char().isdigit()):
                    break  # 点后面不是数字，停止
                has_dot = True
            num_str += self.current_char()
            self.advance()
        
        # 检查数字后面是否紧跟字母或标识符字符
        # 如果是，则这是一个标识符而不是纯数字
        if self.current_char() and (self.current_char().isalpha() or self.current_char() in '_$'):
            # 继续读取作为标识符
            while self.current_char() and (
                self.current_char().isalnum() or 
                self.current_char() in '_$'
            ):
                num_str += self.current_char()
                self.advance()
            
            # 检查是否是关键字
            token_type = self.KEYWORDS.get(num_str.upper(), TokenType.IDENTIFIER)
            return num_str, token_type
        
        return num_str, TokenType.NUMBER
    
    def read_identifier(self) -> Tuple[str, TokenType]:
        """读取标识符或关键字
        
        标识符可以包含：字母、数字、下划线、美元符号
        特殊处理：宏参数可以有默认值 $PARAM|default$
        """
        result = ''
        in_macro = False  # 是否在宏参数内部
        
        while self.current_char():
            char = self.current_char()
            
            # 宏参数开始
            if char == '$':
                result += char
                self.advance()
                in_macro = not in_macro  # 切换宏参数状态
                continue
            
            # 在宏参数内部，允许更多字符（用于默认值）
            # 例如：$PARAM|default$ 或 $AGE|-1$
            if in_macro and char in '|-':
                result += char
                self.advance()
                continue
            
            # 普通标识符字符
            if char.isalnum() or char in '_':
                result += char
                self.advance()
                continue
            
            # 不是标识符字符，结束
            break
        
        # 检查是否是关键字
        token_type = self.KEYWORDS.get(result.upper(), TokenType.IDENTIFIER)
        
        return result, token_type
    
    def read_variable(self) -> str:
        """读取变量引用 @variable_name"""
        result = '@'
        self.advance()  # 跳过 @
        
        while self.current_char() and (
            self.current_char().isalnum() or 
            self.current_char() in '_-'
        ):
            result += self.current_char()
            self.advance()
        
        return result
    
    def read_conditional_param(self) -> str:
        """读取条件参数 [[PARAM]"""
        result = '[['
        self.advance()  # 跳过第一个 [
        self.advance()  # 跳过第二个 [
        
        # 读取到 ] 为止
        while self.current_char() and self.current_char() != ']':
            result += self.current_char()
            self.advance()
        
        if self.current_char() == ']':
            result += ']'
            self.advance()  # 跳过 ]
        
        return result
    
    def tokenize(self) -> List[Token]:
        """执行词法分析"""
        while self.current_char():
            # 记录位置
            line = self.line
            column = self.column
            
            # 跳过空白
            whitespace = self.skip_whitespace()
            
            # 更新位置（跳过空白后）
            line = self.line
            column = self.column
            
            char = self.current_char()
            
            if char is None:
                break
            
            # 注释
            if char == '#':
                comment = self.read_comment()
                self.tokens.append(Token(
                    TokenType.COMMENT, comment, line, column, whitespace
                ))
                continue
            
            # 换行
            if char == '\n':
                self.tokens.append(Token(
                    TokenType.NEWLINE, '\n', line, column, whitespace
                ))
                self.advance()
                continue
            
            # 字符串
            if char in '"\'':
                string_value = self.read_string()
                self.tokens.append(Token(
                    TokenType.STRING, string_value, line, column, whitespace
                ))
                continue
            
            # 数字（包括负数）或数字开头的标识符
            # 负号后面紧跟数字才是负数，否则是减号运算符
            if char.isdigit():
                num_value, token_type = self.read_number()
                self.tokens.append(Token(
                    token_type, num_value, line, column, whitespace
                ))
                continue
            
            # 处理负数：前一个 token 必须是运算符或开始括号
            if char == '-' and self.peek_char() and self.peek_char().isdigit():
                # 检查前一个token，如果是数字或标识符或右括号，这是减号而不是负数
                if self.tokens:
                    last_token = self.tokens[-1]
                    if last_token.type in (TokenType.NUMBER, TokenType.IDENTIFIER, 
                                          TokenType.RPAREN, TokenType.RBRACKET):
                        # 这是减号运算符
                        self.tokens.append(Token(
                            TokenType.MINUS, '-', line, column, whitespace
                        ))
                        self.advance()
                        continue
                
                # 否则是负数（或负数开头的标识符）
                num_value, token_type = self.read_number()
                self.tokens.append(Token(
                    token_type, num_value, line, column, whitespace
                ))
                continue
            
            # @ 符号处理
            if char == '@':
                # 检查下一个字符
                next_char = self.peek_char()
                if next_char == '[':
                    # 这是内联运算 @[ ... ]
                    self.advance()  # 跳过 @
                    self.tokens.append(Token(
                        TokenType.AT, '@', line, column, whitespace
                    ))
                    # [ 会在下一轮循环中被处理
                elif next_char == '\\' and self.peek_char(2) == '[':
                    # 这是带反斜杠的内联运算 @\[ ... ]
                    self.advance()  # 跳过 @
                    self.advance()  # 跳过 \
                    self.tokens.append(Token(
                        TokenType.AT, '@\\', line, column, whitespace
                    ))
                    # [ 会在下一轮循环中被处理
                else:
                    # @ 符号（可能是常量引用或作用域绑定，由 parser 决定）
                    self.tokens.append(Token(
                        TokenType.AT, '@', line, column, whitespace
                    ))
                    self.advance()
                    # 后面的标识符会在下一轮循环中被处理
                continue
            
            # 双字符运算符
            if char == '>' and self.peek_char() == '=':
                self.tokens.append(Token(
                    TokenType.GTE, '>=', line, column, whitespace
                ))
                self.advance()
                self.advance()
                continue
            
            if char == '<' and self.peek_char() == '=':
                self.tokens.append(Token(
                    TokenType.LTE, '<=', line, column, whitespace
                ))
                self.advance()
                self.advance()
                continue
            
            if char == '=' and self.peek_char() == '=':
                self.tokens.append(Token(
                    TokenType.EQUALS_EQUALS, '==', line, column, whitespace
                ))
                self.advance()
                self.advance()
                continue
            
            if char == '!' and self.peek_char() == '=':
                self.tokens.append(Token(
                    TokenType.NOT_EQUALS, '!=', line, column, whitespace
                ))
                self.advance()
                self.advance()
                continue
            
            # 条件参数 [[PARAM]
            if char == '[' and self.peek_char() == '[':
                param_value = self.read_conditional_param()
                self.tokens.append(Token(
                    TokenType.CONDITIONAL_PARAM, param_value, line, column, whitespace
                ))
                continue
            
            # 单字符运算符和符号
            single_char_tokens = {
                '=': TokenType.EQUALS,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                '>': TokenType.GT,
                '<': TokenType.LT,
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.MULTIPLY,
                '/': TokenType.DIVIDE,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '|': TokenType.PIPE,
                '.': TokenType.DOT,
                ':': TokenType.COLON,
            }
            
            if char in single_char_tokens:
                self.tokens.append(Token(
                    single_char_tokens[char], char, line, column, whitespace
                ))
                self.advance()
                continue
            
            # 标识符或关键字（可以以字母、下划线或美元符号开头）
            if char.isalpha() or char in '_$':
                id_value, token_type = self.read_identifier()
                self.tokens.append(Token(
                    token_type, id_value, line, column, whitespace
                ))
                continue
            
            # 未知字符，跳过
            self.advance()
        
        # 添加 EOF
        self.tokens.append(Token(
            TokenType.EOF, '', self.line, self.column, ''
        ))
        
        return self.tokens


# ============================================
# 辅助函数
# ============================================

def lex(text: str) -> List[Token]:
    """便捷函数：执行词法分析"""
    lexer = Lexer(text)
    return lexer.tokenize()


def format_tokens(tokens: List[Token], show_whitespace: bool = False) -> str:
    """格式化 tokens 以便阅读"""
    lines = []
    for token in tokens:
        ws = repr(token.whitespace_before) if show_whitespace else ''
        lines.append(f"{token.line:3}:{token.column:3} {token.type.name:15} {ws} {repr(token.value)}")
    return '\n'.join(lines)


# ============================================
# 测试代码
# ============================================

if __name__ == '__main__':
    # 测试代码
    test_code = """
building_research_lab_1 = {
    base_buildtime = @b1_time
    category = research
    
    cost = {
        minerals = 400
    }
    
    destroy_trigger = {
        OR = {
            owner = { is_ai = yes }
            num_buildings = { type = research value > 1 }
        }
    }
    
    # This is a comment
    upkeep = { energy = 2 }
}
"""
    
    print("输入代码:")
    print("=" * 60)
    print(test_code)
    print("=" * 60)
    
    print("\nTokens:")
    print("=" * 60)
    tokens = lex(test_code)
    
    # 过滤掉注释和换行以便查看
    filtered_tokens = [t for t in tokens if t.type not in (TokenType.COMMENT, TokenType.NEWLINE)]
    print(format_tokens(filtered_tokens))
