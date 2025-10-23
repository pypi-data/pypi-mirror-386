import ast

class ReplaceName(ast.NodeTransformer):
    def __init__(self, old_name, new_name):
        self.old_name = old_name
        self.new_name = new_name

    def visit_Name(self, node):
        if node.id == self.old_name:
            node.id = self.new_name
        return self.generic_visit(node)

def transform(node, old_name, new_name):
    return ReplaceName(old_name, new_name).visit(node)