from pathlib import Path
from .parser import parse, parse_file
from synthetipy.parsing.parser_utils import *
from .ast_nodes import *

# 对初步解析的 AST 进行细化处理，生成更具体的结构
class RefineParser(ParserContextHelper):
    def __init__(self, root: DocumentNode):
        self.root = root

    def parse(self):
        for stmt in self.root.statements:
            if not isinstance(stmt, ObjectNode):
                continue  # 目前只细化对象定义，其他类型暂不处理
            self._refine_object(stmt)
            
    def _refine_object(self, obj: ObjectNode):
        if str(obj.name) == 'inline_script':
            self._parse_inline_script(obj, None, None)  # 直接传入对象本身，后续方法会处理替换
        body = obj.body
        for idx, stmt in enumerate(body.statements):
            self._refine_statement(stmt, body, idx)
            
    def _refine_statement(self, stmt, parent, index):
        if isinstance(stmt, PropertyNode):
            if str(stmt.key) == 'inline_script':
                self._parse_inline_script(stmt, parent, index)
                
                
    def _parse_inline_script(self, node: Union[ObjectNode, PropertyNode], parent, index):
        script_path = None
        params = {}
        assert isinstance(node.value, (LiteralNode, BlockNode)), "Expected literal or block for inline_script value"
        if isinstance(node.value, LiteralNode):
            script_path = node.value
        elif isinstance(node.value, BlockNode):
            for stmt in node.value.statements:
                if isinstance(stmt, PropertyNode):
                    key = str(stmt.key)
                    if key == 'script':
                        # Extract script path
                        assert isinstance(stmt.value, LiteralNode)
                        script_path = stmt.value
                    else:
                        params[key] = stmt.value
                else:
                    assert False, "Expected property in inline_script block"
        new_node = InlineScriptNode(script_path, params)
        self._replace_node(parent, index, new_node)
        
    def _replace_node(self, parent, index, new_node):
        new_node.line = parent.statements[index].line
        new_node.column = parent.statements[index].column
        parent.statements[index] = new_node
        
def refine_ast(root: DocumentNode):
    """对 AST 进行细化处理，生成更具体的结构"""
    refine_parser = RefineParser(root)
    refine_parser.parse()
def refined_parse(source: str) -> DocumentNode:
    """从源代码解析并细化 AST"""
    root = parse(source)
    refine_ast(root)
    return root
def refined_parse_file(file_path: Path) -> DocumentNode:
    """从文件解析并细化 AST"""
    root = parse_file(file_path)
    refine_ast(root)
    return root