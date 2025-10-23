import ast

class RemoveFuncDecorator(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        node.decorator_list = []
        return node

def transform(node):
    return RemoveFuncDecorator().visit(node)