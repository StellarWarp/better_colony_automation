"""
PDXLang Patcher - Inline Script 解析器
处理 Stellaris 的 inline_script 引用和展开
采用 AST 后处理策略：解析后在 AST 层面展开，并添加来源追踪
"""

import re
from pathlib import Path
from typing import Dict, Optional, Union, List, Tuple
from .refine_parser import refined_parse
from .ast_nodes import *
from .inline_script_utils import (
    InlineScriptLoader,
    extract_script_info,
    replace_parameters,
    is_inline_script,
)


class InlineScriptResolver:
    """Inline Script 解析和展开器（AST 后处理）"""
    
    def __init__(self, game_root: Union[str, Path]):
        """
        初始化解析器
        
        Args:
            game_root: Stellaris 游戏根目录
        """
        self.game_root = Path(game_root)
        self.loader = InlineScriptLoader(game_root)
        self.scripts_root = self.game_root / "common" / "inline_scripts"
        self.expansion_depth = 0  # 当前展开深度，用于防止无限递归
    
    def load_script(self, script_path: str) -> Optional[str]:
        """加载 inline_script 文件"""
        return self.loader.load(script_path)
    
    def _replace_parameters(self, text: str, params: Dict[str, str]) -> str:
        """替换参数占位符（兼容接口）"""
        return replace_parameters(text, params)
    
    def _extract_params_from_ast(self, node: InlineScriptNode) -> Tuple[Optional[str], Dict[str, str]]:
        """从 AST 节点提取脚本信息"""
        return extract_script_info(node)
    
    def _is_inline_script(self, node: ASTNode) -> bool:
        """检查节点是否是 inline_script"""
        return is_inline_script(node)
    
    def _add_source_metadata(self, node: ASTNode, source_file: str, original_line: int):
        """
        为节点添加来源元数据
        
        Args:
            node: AST 节点
            source_file: 来源文件路径
            original_line: 原始行号
        """
        if not hasattr(node, '_metadata'):
            node._metadata = {}
        node._metadata['source_file'] = source_file
        node._metadata['source_line'] = original_line
        node._metadata['is_expanded'] = True
    
    def expand_ast_node(self, node: InlineScriptNode) -> List[ASTNode]:
        """
        展开单个 inline_script 节点为多个语句
        
        Args:
            node: inline_script 属性节点
            
        Returns:
            展开后的语句列表
        """
        # 提取参数
        script_path, params = self._extract_params_from_ast(node)
        
        if not script_path:
            raise ValueError(f"Could not extract script path from inline_script at line {node.line}")
        
        # 加载脚本文本
        script_text = self.load_script(script_path)
        if not script_text:
            raise FileNotFoundError(f"Inline script not found: {script_path}")
        
        # 替换参数（文本级别）
        if params:
            script_text = self._replace_parameters(script_text, params)
        

        wrapped = f"_wrapper = {{\n{script_text}\n}}"
        ast = refined_parse(wrapped)
        
        if not ast.statements or not isinstance(ast.statements[0], ObjectNode):
            raise ValueError(f"Parsed inline script does not contain expected object structure: {script_path}")
        
        statements = ast.statements[0].body.statements
        
        # 为展开的节点添加来源元数据
        source_file = f"inline_scripts/{script_path}.txt"
        for stmt in statements:
            self._add_source_metadata(stmt, source_file, stmt.line if hasattr(stmt, 'line') else 0)
        
        # 递归展开（如果有嵌套的 inline_script）
        # 注意：我们需要像 expand_block 那样处理，因为可能有嵌套的 inline_script 需要1→N展开
        self.expansion_depth += 1
        if self.expansion_depth < 10:  # 防止无限递归
            expanded_statements = []
            for stmt in statements:
                if self._is_inline_script(stmt):
                    # 嵌套的 inline_script，递归展开为多个语句
                    nested_expanded = self.expand_ast_node(stmt)
                    expanded_statements.extend(nested_expanded)
                else:
                    # 普通语句，递归处理其内部
                    expanded = self.expand_statement(stmt)
                    expanded_statements.append(expanded)
            statements = expanded_statements
        self.expansion_depth -= 1
        
        return statements
            
   
    
    def expand_statement(self, node: ASTNode) -> ASTNode:
        """
        递归展开语句中的 inline_script
        
        Args:
            node: AST 节点
            
        Returns:
            展开后的节点（注意：如果是 inline_script，应该在 expand_block 中处理）
        """
        if isinstance(node, PropertyNode):
            # ⚠️ 注意：这里不应该单独遇到 inline_script PropertyNode
            # inline_script 应该在 expand_block 中被1→N展开
            # 这里只是递归处理值部分
            new_value = self.expand_statement(node.value)
            new_prop = PropertyNode(node.key, new_value)
            new_prop.line = node.line
            new_prop.column = node.column
            if hasattr(node, '_metadata'):
                new_prop._metadata = node._metadata
            return new_prop
            
        elif isinstance(node, BlockNode):
            return self.expand_block(node)
            
        elif isinstance(node, ConditionNode):
            new_body = self.expand_statement(node.body)
            new_cond = ConditionNode(node.operator, new_body)
            new_cond.line = node.line
            new_cond.column = node.column
            if hasattr(node, '_metadata'):
                new_cond._metadata = node._metadata
            return new_cond
            
        elif isinstance(node, ObjectNode):
            new_body = self.expand_statement(node.body)
            new_obj = ObjectNode(node.name, new_body)
            new_obj.line = node.line
            new_obj.column = node.column
            if hasattr(node, '_metadata'):
                new_obj._metadata = node._metadata
            return new_obj
            
        else:
            # 其他类型直接返回
            return node
    
    def expand_block(self, block: BlockNode) -> BlockNode:
        """
        展开 BlockNode 中的所有 inline_script
        
        Args:
            block: 代码块节点
            
        Returns:
            展开后的代码块
        """
        new_statements = []
        
        for stmt in block.statements:
            if self._is_inline_script(stmt):
                # 展开为多个语句
                expanded = self.expand_ast_node(stmt)
                new_statements.extend(expanded)
            else:
                # 递归处理其他语句
                expanded = self.expand_statement(stmt)
                new_statements.append(expanded)
        
        new_block = BlockNode(new_statements)
        new_block.line = block.line
        new_block.column = block.column
        if hasattr(block, '_metadata'):
            new_block._metadata = block._metadata
        
        return new_block
    
    def expand_document(self, document: DocumentNode) -> DocumentNode:
        """
        展开文档中的所有 inline_script
        
        Args:
            document: 文档节点
            
        Returns:
            展开后的文档节点
        """
        new_statements = []
        
        for stmt in document.statements:
            expanded = self.expand_statement(stmt)
            new_statements.append(expanded)
        
        return DocumentNode(new_statements)


# 便捷函数

def create_resolver(game_root: Union[str, Path]) -> InlineScriptResolver:
    """创建 inline script 解析器"""
    return InlineScriptResolver(game_root)


# 测试代码
if __name__ == '__main__':
    import sys
    from pathlib import Path
    
    # 添加 src 目录到 sys.path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))
    
    print("=" * 60)
    print("测试 Inline Script Resolver (AST 后处理)")
    print("=" * 60)
    
    # 创建解析器
    game_root = Path("D:/SteamLibrary/steamapps/common/Stellaris")
    
    if not game_root.exists():
        print(f"\n错误: 游戏目录不存在: {game_root}")
        sys.exit(1)
    
    resolver = InlineScriptResolver(game_root)
    
    # 测试加载脚本
    print("\n测试 1: 加载 inline_script")
    print("-" * 60)
    
    script = resolver.load_script("jobs/roboticist_add")
    if script:
        print(f"成功加载 jobs/roboticist_add")
        print(f"内容长度: {len(script)} 字符")
        print(f"前 200 字符:\n{script[:200]}")
    else:
        print("加载失败")
    
    # 测试 AST 展开
    print("\n测试 2: AST 级别展开")
    print("-" * 60)
    
    code = """
building_test = {
    cost = { minerals = 400 }
    inline_script = jobs/roboticist_add
}
"""
    
    # 解析
    ast = refined_parse(code)
    print(f"解析完成，对象数: {len(ast.statements)}")
    
    # 展开
    expanded_ast = resolver.expand_document(ast)
    print(f"展开完成，对象数: {len(expanded_ast.statements)}")
    
    # 检查第一个对象的语句数
    if expanded_ast.statements:
        obj = expanded_ast.statements[0]
        if isinstance(obj, ObjectNode):
            print(f"第一个对象语句数: {len(obj.body.statements)}")
            
            # 检查元数据
            for i, stmt in enumerate(obj.body.statements[:3]):
                if hasattr(stmt, '_metadata'):
                    meta = stmt._metadata
                    print(f"  语句 {i+1}: 来源={meta.get('source_file')}, 行号={meta.get('source_line')}")
    
    # 编译查看结果
    try:
        from synthetipy import compile_ast
        compiled = compile_ast(expanded_ast)
        print(f"\n编译后代码（前 500 字符）:")
        print(compiled[:500])
    except ImportError as e:
        print(f"\n编译器模块未找到: {e}，跳过编译测试")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
