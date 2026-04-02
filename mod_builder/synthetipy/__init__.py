"""
PDXLang Patcher - Paradox 脚本语言的 Python 工具链
为 Stellaris Mod 开发提供类似编译器的元编程能力

作者: Estelle
版本: 0.1.0-alpha
许可: MIT
"""

__version__ = '0.1.0-alpha'
__author__ = 'Estelle'

# 导出核心类和函数
from .parsing.lexer import Lexer, lex, Token, TokenType
from .parser import Parser, parse
from .compiler import Compiler, compile_ast, compile_to_file
from .inline_script_resolver import InlineScriptResolver, create_resolver
from .inline_script_utils import (
    InlineScriptLoader,
    extract_script_info,
    replace_parameters,
    is_inline_script,
    format_meta_inline_script,
)
from .config import Config, get_config
from . import pdx_constants
from .ast_nodes import (
    # 节点类
    ASTNode,
    DocumentNode,
    ObjectNode,
    PropertyNode,
    BlockNode,
    LiteralNode,
    ListNode,
    ConditionNode,
    ComparisonNode,
    InlineScriptNode,
    CommentNode,
    ConditionalParamNode,
    DirectiveNode,
    ConstantNode,
    ConstantDefinitionNode,
    IdentifierExpressionNode,
    InlineArithmeticNode,
    # 新增节点
    ScopeNode,
    
)

# 访问者类（在 ast_utils.py 中）
from .ast_utils import ASTVisitor, ASTTransformer, create_property, dict_to_block, block_to_dict


__all__ = [
    # 版本信息
    '__version__',
    '__author__',
    
    # 词法分析
    'Lexer',
    'lex',
    'Token',
    'TokenType',
    
    # 语法分析
    'Parser',
    'parse',
    
    # 代码生成/编译
    'Compiler',
    'compile_ast',
    'compile_to_file',
    
    # Inline Script 解析
    'InlineScriptResolver',
    'create_resolver',
    
    # AST 节点
    'ASTNode',
    'DocumentNode',
    'ObjectNode',
    'PropertyNode',
    'BlockNode',
    'LiteralNode',
    'ListNode',
    'ConditionNode',
    'ComparisonNode',
    'InlineScriptNode',
    'CommentNode',
    'ConditionalParamNode',
    'DirectiveNode',
    'ConstantNode',
    'ConstantDefinitionNode',
    'IdentifierExpressionNode',
    'InlineArithmeticNode',
    
    # 访问者模式
    'ASTVisitor',
    'ASTTransformer',
    
    # 辅助函数
    'create_property',
    'dict_to_block',
    'block_to_dict',

    # 'Building',
    # 'ScriptedTrigger',
    # 'scripted_trigger',
    # 'scripted_effect',
    # 'building',
    # 'OR',
    # 'AND',
    # 'NOT',
]


def get_info():
    """获取包信息"""
    return {
        'name': 'SynthetiPy',
        'version': __version__,
        'author': __author__,
        'description': 'Paradox 脚本语言的 Python 工具链',
        'license': 'GNU LGPL v3',
        'status': 'alpha - 仅实现了词法分析器和 AST 定义',
    }


if __name__ == '__main__':
    print("SynthetiPy")
    print("=" * 50)
    info = get_info()
    for key, value in info.items():
        print(f"{key:12}: {value}")
