import ast

class WhereToTernary(ast.NodeTransformer):
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'where':
            assert len(node.args) == 3
            newnode = ast.IfExp(
                test=node.args[0],
                body=node.args[1],
                orelse=node.args[2],
            )
            newnode.lineno = node.lineno
            node = newnode
        return node

def transform(node):
    return WhereToTernary().visit(node)