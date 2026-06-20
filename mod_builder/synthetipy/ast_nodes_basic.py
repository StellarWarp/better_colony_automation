
from typing import Any, List, Dict, Optional, Union
from abc import ABC, abstractmethod


class ASTNode(ABC):
    """AST 节点基类"""
    
    def __init__(self, line: int = 0, column: int = 0):
        self.line = line
        self.column = column
        self.parent: Optional[ASTNode] = None
    
    @abstractmethod
    def accept(self, visitor):
        """访问者模式接口"""
        pass
    
    def __repr__(self):
        return f"{self.__class__.__name__}()"

class WrappedString(ASTNode):
    def __init__(self, value: str):
        super().__init__()
        self.value = value
        
    def accept(self, visitor):
        return visitor.visit_wraped_string(self)
    
    def __repr__(self):
        return f"'{self.value}'"
    
    def __str__(self):
        return self.value

class DocumentNode(ASTNode):
    """文档根节点 - 包含所有顶层语句"""
    
    def __init__(self, statements: List[ASTNode]):
        super().__init__()
        self.statements = statements
        for stmt in statements:
            stmt.parent = self
    
    def accept(self, visitor):
        return visitor.visit_document(self)
    
    def __repr__(self):
        return f"Document({len(self.statements)} statements)"


class ObjectNode(ASTNode):
    """顶层对象定义
    
    例如:
        building_research_lab_1 = {
            category = research
            cost = { minerals = 400 }
        }
        tech_$AREA$_1 = { ... }  # 宏参数
    """
    
    def __init__(self, name: Any, body: 'BlockNode'):
        super().__init__()
        self.name = name
        self.body = body
        body.parent = self
        if isinstance(name, ASTNode):
            name.parent = self
    
    def accept(self, visitor):
        return visitor.visit_object(self)
    
    def __repr__(self):
        name_str = str(self.name) if isinstance(self.name, str) else repr(self.name)
        return f"Object({name_str})"


class PropertyNode(ASTNode):
    """属性（键值对）
    
    例如:
        category = research
        cost = { minerals = 400 }
        tech_$AREA$ = value  # 宏参数
    """
    
    def __init__(self, key: Any, value: ASTNode):
        super().__init__()
        if isinstance(key, str):
            key = WrappedString(key)
        elif isinstance(key, ASTNode):
            self.key = key
        else:
            assert False, f"Invalid key type for PropertyNode: {type(key)}"
        key.parent = self
        self.value = value
        value.parent = self
    
    def accept(self, visitor):
        return visitor.visit_property(self)
    
    def __repr__(self):
        key_str = str(self.key) if isinstance(self.key, str) else repr(self.key)
        return f"Property({key_str} = {self.value})"


class BlockNode(ASTNode):
    """代码块 { ... }
    
    包含多个语句的代码块
    """
    
    def __init__(self, statements: List[ASTNode]):
        super().__init__()
        self.statements = statements
        for stmt in statements:
            stmt.parent = self
    
    def accept(self, visitor):
        return visitor.visit_block(self)
    
    def get_property(self, key: str) -> Optional[PropertyNode]:
        """获取指定键的属性"""
        for stmt in self.statements:
            if isinstance(stmt, PropertyNode) and str(stmt.key) == key:
                return stmt
        return None
    
    def add_property(self, key: str, value: ASTNode):
        """添加新属性"""
        prop = PropertyNode(key, value)
        self.statements.append(prop)
        prop.parent = self
    
    def remove_property(self, key: str):
        """移除属性"""
        self.statements = [
            stmt for stmt in self.statements 
            if not (isinstance(stmt, PropertyNode) and str(stmt.key) == key)
        ]
    
    def __repr__(self):
        return f"Block({len(self.statements)} statements)"


class LiteralNode(ASTNode):
    class Color:
        def __init__(self, color_type: str, values: List[int]):
            self.color_type = color_type  # 'rgb' 或 'hsv'
            self.values = values  # 例如 [255, 0, 128] 或 [360, 100, 100]
        
        def __repr__(self):
            return f"Color(type={self.color_type}, values={self.values})"
        def __str__(self):
            return f"{self.color_type} {{ {self.values[0]} {self.values[1]} {self.values[2]} }}"
            
    """字面量节点（编译时常量值）
    
    支持的类型:
        - int: 100
        - float: 3.14
        - bool: yes, no (PDX 语法)
        - string: "some text"
        - identifier: research (枚举值/标识符常量)
        - constant: @b1_time (编译时常量引用)
    """
    
    def __init__(self, value: Union[int, float, bool, str, Color], value_type: str = 'auto'):
        super().__init__()
        self.raw_value = value
        
        # 自动推断类型
        if value_type == 'auto':
            if isinstance(value, bool):
                self.value_type = 'bool'
                self.value = value
            elif isinstance(value, int):
                self.value_type = 'int'
                self.value = value
            elif isinstance(value, float):
                self.value_type = 'float'
                self.value = value
            elif isinstance(value, str):
                # 检查是否是布尔值
                if value.lower() in 'yes':
                    self.value_type = 'bool'
                    self.value = True
                elif value.lower() in 'no':
                    self.value_type = 'bool'
                    self.value = False
                # 检查是否是数字
                elif value.replace('.', '').replace('-', '').isdigit():
                    if '.' in value:
                        self.value_type = 'float'
                        self.value = float(value)
                    else:
                        self.value_type = 'int'
                        self.value = int(value)
                # 检查是否是变量引用
                elif value.startswith('@'):
                    self.value_type = 'constant'
                    self.value = value
                else:
                    self.value_type = 'identifier'
                    self.value = value
            elif isinstance(value, self.Color):
                self.value_type = 'color'
                self.value = value
        else:
            self.value_type = value_type
            self.value = value
    
    def accept(self, visitor):
        return visitor.visit_literal(self)
    
    def __repr__(self):
        return f"Literal({self.value}, type={self.value_type})"
    
    def __str__(self):
        if self.value_type == 'bool':
            return 'yes' if self.value else 'no'
        elif self.value_type == 'string':
            return f'"{self.value}"'
        else:
            return str(self.value)


class ListNode(ASTNode):
    """列表 { item1 item2 item3 }
    
    包含多个值的列表（不是键值对）
    """
    
    def __init__(self, items: List[Any]):
        super().__init__()
        self.items = items
        for item in items:
            item.parent = self
    
    def accept(self, visitor):
        return visitor.visit_list(self)
    
    def __repr__(self):
        return f"List({len(self.items)} items)"


class ConditionNode(ASTNode):
    """逻辑条件块
    
    例如:
        OR = {
            has_technology = tech_advanced
            owner = { is_ai = yes }
        }

        OR = {
            tech_autocurating_vault
            tech_transcendent_faith
        }
    """
    
    OPERATORS = ['OR', 'AND', 'NOT', 'NAND', 'NOR']
    
    def __init__(self, operator: Union[str, WrappedString], body: ASTNode):
        super().__init__()
        assert isinstance(operator, (str, WrappedString)), "Operator should be a string or WrappedString"
        if isinstance(operator, str):
            assert operator in self.OPERATORS, f"Invalid operator: {operator}"
            self.operator = WrappedString(operator)
        else:
            assert operator.value in self.OPERATORS, f"Invalid operator: {operator.value}"
            self.operator = operator
        assert isinstance(body, (BlockNode, ListNode)), "Condition body should be a BlockNode or ListNode"
        self.operator.parent = self
        self.body = body
        body.parent = self
    
    def accept(self, visitor):
        return visitor.visit_condition(self)
    
    def __repr__(self):
        return f"Condition({self.operator})"


class ComparisonNode(ASTNode):
    """比较表达式
    
    例如:
        minerals > 1000
        num_pops >= 50
        is_ai = yes
        tech_$AREA$ > 10  # 宏参数
    """
    
    OPERATORS = ['=', '>', '<', '>=', '<=', '==', '!=']
    
    def __init__(self, left, operator: Union[str, WrappedString], right: ASTNode):
        super().__init__()
        assert isinstance(operator, (str, WrappedString)), "Operator should be a string or WrappedString"
        if isinstance(operator, str):
            assert operator in self.OPERATORS, f"Invalid operator: {operator}"
            self.operator = WrappedString(operator)
        else:
            assert operator.value in self.OPERATORS, f"Invalid operator: {operator.value}"
            self.operator = operator
        self.operator.parent = self
        self.left = left
        self.right = right
        right.parent = self
        if isinstance(left, ASTNode):
            left.parent = self
    
    def accept(self, visitor):
        return visitor.visit_comparison(self)
    
    def __repr__(self):
        left_str = str(self.left) if isinstance(self.left, str) else repr(self.left)
        return f"Comparison({left_str} {self.operator} {self.right})"


class InlineScriptNode(ASTNode):
    """内联脚本调用
    
    例如:
        inline_script = {
            script = jobs/researcher_add
            AMOUNT = 10
        }
    """
    
    def __init__(self, script_path: LiteralNode, parameters: Dict[str, Any]):
        super().__init__()
        assert isinstance(script_path, LiteralNode), "script_path should be a LiteralNode"
        self.script_path = script_path
        self.parameters = parameters
    
    def accept(self, visitor):
        return visitor.visit_inline_script(self)
    
    def __repr__(self):
        return f"InlineScript('{self.script_path}')"


class CommentNode(ASTNode):
    """注释
    
    支持:
        # 单行注释
    """
    
    def __init__(self, text: str, is_inline: bool = False):
        super().__init__()
        self.text = text
        self.is_inline = is_inline  # 行尾注释 vs 独立行注释
    
    def accept(self, visitor):
        return visitor.visit_comment(self)
    
    def __repr__(self):
        return f"Comment('{self.text[:20]}...')"


class DirectiveNode(ASTNode):
    """系统指令/标记节点
    
    某些标识符本身就是有效的语句，不需要值
    例如:
        optimize_memory
        clear_all_variables
    """
    
    def __init__(self, name: str):
        super().__init__()
        assert isinstance(name, str), "name should be a string"
        self.name = WrappedString(name)
        self.name.parent = self
    
    def accept(self, visitor):
        return visitor.visit_directive(self)
    
    def __repr__(self):
        return f"Directive('{self.name}')"


class ConditionalParamNode(ASTNode):
    """条件参数块
    
    例如:
        [[SPIRITUALIST]
            is_spiritualist = yes
        ]
        [[!SPIRITUALIST]
            is_spiritualist = no
        ]
    """
    
    def __init__(self, param_name: str, body: List[ASTNode]):
        super().__init__()
        assert isinstance(param_name, str), "param_name should be a string"
        self.param_name = WrappedString(param_name)  # 例如 "SPIRITUALIST" 或 "!SPIRITUALIST"
        self.param_name.parent = self
        self.body = body
        for stmt in body:
            stmt.parent = self
    
    def accept(self, visitor):
        return visitor.visit_conditional_param(self)
    
    def __repr__(self):
        return f"ConditionalParam('[[{self.param_name}]')"


class ConstantNode(ASTNode):
    """常量引用（编译时确定的值）
    
    例如:
        @b1_time
        @b1_minerals
    
    注意：这是脚本中定义的常量，不是运行时变量
    """
    
    def __init__(self, name: str):
        super().__init__()
        assert isinstance(name, str), "name should be a string"
        self.name = WrappedString(name)  # 例如 "@b1_time"
        self.name.parent = self
    
    def accept(self, visitor):
        return visitor.visit_constant(self)
    
    def __repr__(self):
        return f"Constant('{self.name}')"


class ConstantDefinitionNode(ASTNode):
    """常量定义（编译时静态常量）
    
    例如:
        @buildings_t1 = 240
        @b1_time = 360
        @stabilitylevel2 = 40
    
    注意：这是常量的定义，不是变量。值在编译时确定。
    """
    
    def __init__(self, name: str, value: ASTNode):
        super().__init__()
        assert isinstance(name, str), "name should be a string"
        self.name = WrappedString(name)  # 例如 "@buildings_t1"
        self.name.parent = self
        self.value = value
        value.parent = self
    
    def __repr__(self) -> str:
        return f"ConstantDefinition({self.name} = {self.value})"
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_constant_definition(self)

class InlineArithmeticNode(ASTNode):
    r"""内联算术表达式
    
    表示 @[ expr ] 或 @\[ expr ] 形式的内联计算
    例如:
        @[( 72 * $PROGRESS$ )]
        @\[( value + 10 )]
    
    目前保存原始表达式文本，不解析内部结构
    """
    
    def __init__(self, expression: str, escaped: bool = False):
        super().__init__()
        self.expression = expression  # 原始表达式文本（不含 @[ 和 ]）
        self.escaped = escaped  # 是否是 @\[ 形式
    
    def __repr__(self) -> str:
        prefix = '@\\[' if self.escaped else '@['
        return f"InlineArithmetic('{prefix}{self.expression}]')"
    
    def accept(self, visitor: 'ASTVisitor'):
        return visitor.visit_inline_arithmetic(self)



