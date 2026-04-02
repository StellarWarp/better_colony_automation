"""
PDXLang Parser Utilities - 解析器辅助工具

包含错误处理、上下文获取等通用功能
"""

from typing import Optional, List
from .lexer import Token, TokenType


class ParserError(Exception):
    """解析错误"""
    def __init__(self, message: str, token: Optional[Token] = None, context: str = None):
        self.token = token
        self.context = context
        
        # 构建详细的错误信息
        error_parts = [message]
        
        if token:
            error_parts.append(f"at line {token.line}, column {token.column}")
            
            # 添加 token 信息
            if token.type:
                error_parts.append(f"(token: {token.type.name} '{token.value}')")
        
        # 添加上下文
        if context:
            error_parts.append(f"\nContext: {context}")
        
        super().__init__(" ".join(error_parts))


class ParserContextHelper:
    """解析器上下文辅助类
    
    提供错误信息格式化和源代码上下文提取功能
    """
    
    def __init__(self, source_text: str = None, tokens: List[Token] = None):
        self.source_lines = source_text.splitlines() if source_text else []
        self.tokens = tokens or []
    
    def get_source_context(self, token: Optional[Token] = None, radius: int = 2) -> str:
        """获取指定 token 周围的源代码上下文
        
        Args:
            token: 目标 token
            radius: 前后各显示多少行
        
        Returns:
            格式化的上下文字符串，包含行号和错误标记
        """
        if not token:
            return "<no context>"
        
        # 如果没有源代码，回退到 token 显示
        if not self.source_lines:
            return self._get_token_context(token)
        
        error_line = token.line
        error_col = token.column
        
        # 计算显示范围（注意：行号是从 1 开始的）
        start_line = max(1, error_line - radius)
        end_line = min(len(self.source_lines), error_line + radius)
        
        # 构建上下文显示
        lines = []
        max_line_num_width = len(str(end_line))
        
        for line_num in range(start_line, end_line + 1):
            line_index = line_num - 1  # 转换为 0-based 索引
            if line_index >= len(self.source_lines):
                break
            
            line_content = self.source_lines[line_index]
            line_num_str = str(line_num).rjust(max_line_num_width)
            
            # 错误行用箭头标记
            if line_num == error_line:
                lines.append(f"  {line_num_str} | {line_content}")
                # 添加指示符指向错误列
                # 计算缩进：前导空格(2) + 行号宽度 + " | "(3) + 错误列位置
                indent = ' ' * (2 + max_line_num_width + 3 + error_col - 1)
                lines.append(f"{indent}^--- here")
            else:
                lines.append(f"  {line_num_str} | {line_content}")
        
        return "\n" + "\n".join(lines)
    
    def _get_token_context(self, token: Token, radius: int = 5) -> str:
        """备用方法：当没有源代码时，显示 token 上下文"""
        if not self.tokens:
            return f"<token: {token.type.name} '{token.value}'>"
        
        # 查找 token 在列表中的位置
        try:
            token_index = self.tokens.index(token)
        except ValueError:
            return f"<token: {token.type.name} '{token.value}'>"
        
        start = max(0, token_index - radius)
        end = min(len(self.tokens), token_index + radius + 1)
        
        context_parts = []
        for i in range(start, end):
            t = self.tokens[i]
            if t.type == TokenType.NEWLINE:
                continue
            
            if i == token_index:
                context_parts.append(f">>>{t.value}<<<")
            else:
                context_parts.append(t.value)
        
        return " ".join(context_parts)
    
    def create_error(
        self, 
        message: str, 
        token: Optional[Token] = None,
        expected: str = None, 
        got: str = None
    ) -> ParserError:
        """创建格式化的解析错误
        
        Args:
            message: 基本错误信息
            token: 出错位置的 token
            expected: 期望的内容（可选）
            got: 实际得到的内容（可选）
        
        Returns:
            ParserError 异常对象
        """
        # 构建错误消息
        error_msg = message
        
        if expected and got:
            error_msg = f"{message}: expected {expected}, got {got}"
        elif expected:
            error_msg = f"{message}: expected {expected}"
        
        # 获取上下文
        context = self.get_source_context(token)
        
        return ParserError(error_msg, token, context)


# 系统级指令/标记列表
# 这些标识符单独出现时是有效的语句，不需要 = value
SYSTEM_DIRECTIVES = {
    'optimize_memory',
    'clear_all_variables',
    # 可以继续添加其他系统指令
}
