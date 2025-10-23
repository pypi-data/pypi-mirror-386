import ast
from ..utils import *

class AddFuncDecorator(ast.NodeTransformer):
    def __init__(self, decorator):
        self.decorator = decorator

    def visit_FunctionDef(self, node):
        node.decorator_list.append(new_ast_node_from_str(self.decorator))
        return node

def transform(node, decorator):
    return AddFuncDecorator(decorator).visit(node)
