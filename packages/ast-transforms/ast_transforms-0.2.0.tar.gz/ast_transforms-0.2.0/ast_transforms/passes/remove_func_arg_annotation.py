import ast

class RemoveFuncArgAnnotation(ast.NodeTransformer):
    def visit_arguments(self, node):
        for arg in node.args:
            arg.annotation = None
        return node

def transform(node):
    return RemoveFuncArgAnnotation().visit(node)