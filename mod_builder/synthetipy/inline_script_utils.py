"""
InlineScript 公共工具模块

提供 inline_script 处理的共用功能：
- 参数提取
- 参数替换
- 脚本加载
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union, Any

from .ast_nodes import (
    ASTNode, PropertyNode, BlockNode, LiteralNode, 
    InlineScriptNode, IdentifierExpressionNode
)


class InlineScriptLoader:
    """脚本加载器（带缓存）"""
    
    def __init__(self, game_root: Union[str, Path]):
        self.game_root = Path(game_root)
        self.scripts_root = self.game_root / "common" / "inline_scripts"
        self._cache: Dict[str, str] = {}
    
    def load(self, script_path: str) -> Optional[str]:
        """
        加载 inline_script 文件
        
        Args:
            script_path: 脚本路径，如 "jobs/roboticist_add"
        
        Returns:
            脚本文本内容，不存在则返回 None
        """
        # script_path 可能带了双引号，先去掉
        script_path = str(script_path).strip('"')
        
        if script_path in self._cache:
            return self._cache[script_path]
        
        script_file = self.scripts_root / f"{script_path}.txt"
        
        if not script_file.exists():
            raise FileNotFoundError(f"Inline script not found: {script_file}")
        

        with open(script_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        self._cache[script_path] = content
        return content

    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()


def extract_script_info(node: InlineScriptNode) -> Tuple[str, Dict[str, Any]]:
    """
    从 inline_script 属性节点提取脚本路径和参数
    
    Args:
        node: inline_script 属性节点
    
    Returns:
        (script_path, parameters) 元组
    """
    return node.script_path, node.parameters


def replace_parameters(text: str, params: Dict[str, Any]) -> str:
    """
    替换文本中的参数占位符 $PARAM$
    
    Args:
        text: 原始文本
        params: 参数字典
    
    Returns:
        替换后的文本
    """
    result = text
    for key, value in params.items():
        result = result.replace(f"${key}$", _format_inline_script_param(value))
    return result


def is_inline_script(node: ASTNode) -> bool:
    """检查节点是否是 inline_script"""
    return isinstance(node, InlineScriptNode)


def _format_inline_script_param(value: Any) -> str:
    """Format an inline script argument for textual macro replacement."""
    if isinstance(value, LiteralNode):
        if value.value_type == "string":
            return str(value.value)
        return str(value)
    if isinstance(value, ASTNode):
        from .compiler import compile_ast

        return compile_ast(value)
    return str(value)


def format_meta_inline_script(script_path: str, params: Dict[str, Any]) -> str:
    """
    格式化为 meta.inline_script(...) 调用
    
    Args:
        script_path: 脚本路径
        params: 参数字典
    
    Returns:
        格式化的调用字符串
    """
    if params:
        params_str = ", ".join(f"{k}={_format_literal(v)}" for k, v in params.items())
        return f"meta.inline_script(script='{script_path}', {params_str})"
    return f"meta.inline_script(script='{script_path}')"


def _extract_value(node: ASTNode) -> Any:
    """提取节点的值"""
    if isinstance(node, LiteralNode):
        return node.value
    elif isinstance(node, IdentifierExpressionNode):
        return node.expression
    elif hasattr(node, 'value'):
        return node.value
    return str(node)


def _format_literal(value: Any) -> str:
    """格式化值为 Python 代码"""
    if isinstance(value, bool):
        return str(value)
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        # 尝试解析为数字
        try:
            int(value)
            return value
        except ValueError:
            try:
                float(value)
                return value
            except ValueError:
                return f"'{value}'"
    return f"'{value}'"
