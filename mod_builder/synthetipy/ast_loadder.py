from collections import defaultdict
from pathlib import Path

from synthetipy.ast_nodes_basic import *
from synthetipy.inline_script_resolver import InlineScriptResolver
from synthetipy.refine_parser import refined_parse, refined_parse_file


FOLDER_EXCLUDE = 'exclude'
FOLDER_ORDERED = 'ordered'
FOLDER_UNORDERED = 'unordered'

EXAMPLE_CONFIG = {
    'common': {
        "buildings"
    },
}
     
class ASTLoader:
    def __init__(self, game_root: Path, folder_config: Dict):
        # 统一把 game_root 作为来源列表的第一个
        # 索引: logical_file_path -> object_key -> Object
        self.object_registry: Dict[str, Dict[str, ObjectNode]] = defaultdict(lambda: defaultdict(dict))
        self.game_root = Path(game_root)
        self.folder_config = folder_config

    def load(self) -> Dict[str, Dict[str, ObjectNode]]:
        root = self.game_root

        for primary_folder, folder_config in self.folder_config.items():
                # Iterate folder in root/primary_folder
                folder_path: Path = root / primary_folder
                for folder_name in folder_config:
                    folder: Path = folder_path / folder_name      
                    for file in folder.iterdir():
                        if not file.name.endswith(".txt"): continue
                        full = file
                        rel_logical_path = folder.relative_to(root).as_posix() # e.g. "scripted_effects"
                        self._parse_and_extract(full, rel_logical_path)
        return self.object_registry

    def _parse_and_extract(self, full_path: Path, rel_logical_path: str, unfold_inline_script: bool = True):
        ast = refined_parse_file(full_path)
        if unfold_inline_script:
            ast = InlineScriptResolver(self.game_root).expand_document(ast)
        objects = {}
        for stmt in ast.statements:
            if isinstance(stmt, ObjectNode):
                stmt.parent = None # disassociate from DocumentNode
                objects[str(stmt.name)] = stmt
        file_name = full_path.name
        for key, node in objects.items():
            self.object_registry[rel_logical_path][key] = node

