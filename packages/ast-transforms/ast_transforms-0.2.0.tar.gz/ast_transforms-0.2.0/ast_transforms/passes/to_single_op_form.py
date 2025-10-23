import ast
from ..utils import *

class BinaryOpToAssign(ast.NodeTransformer):
    var_count = 0

    def __init__(self):
        self.stmts = []

    def get_new_var(self):
        BinaryOpToAssign.var_count += 1
        return '__v%d' % BinaryOpToAssign.var_count

    def visit_Call(self, node):
        self.generic_visit(node)
        node = new_ast_assign(
            target = new_ast_name(self.get_new_var(), ctx = ast.Store()),
            value = node
        )
        self.stmts.append(node)
        return node

    def visit_BinOp(self, node):
        newleft = self.visit(node.left)
        newright = self.visit(node.right)
        # newleft and newright now may be statements
        if isinstance(newleft, ast.Assign):
            node.left = ast.Name(id = newleft.targets[0].id, ctx = ast.Load())
        else:
            node.left = newleft

        if isinstance(newright, ast.Assign):
            node.right = ast.Name(id = newright.targets[0].id, ctx = ast.Load())
        else:
            node.right = newright

        #assign = ast.Assign(targets = [ast.Name(id = self.get_new_var(), ctx = ast.Store())], value = node, lineno = node.lineno, col_offset = node.col_offset)
        assign = new_ast_assign(
            target = new_ast_name(self.get_new_var(), ctx = ast.Store()),
            value = node
        )
        self.stmts.append(assign)
        return assign

    def visit_Compare(self, node):
        assert len(node.comparators) == 1
        newleft = self.visit(node.left)
        newright = self.visit(node.comparators[0])
        # newleft and newright now may be statements
        if isinstance(newleft, ast.Assign):
            node.left = ast.Name(id = newleft.targets[0].id, ctx = ast.Load())
        else:
            node.left = newleft

        if isinstance(newright, ast.Assign):
            node.right = ast.Name(id = newright.targets[0].id, ctx = ast.Load())
        else:
            node.right = newright

        assign = ast.Assign(targets = [ast.Name(id = self.get_new_var(), ctx = ast.Store())], value = node, lineno = node.lineno, col_offset = node.col_offset)
        self.stmts.append(assign)
        return assign


class ToSingleOperatorStmts(ast.NodeTransformer):
    def visit_Assign(self, node):
        if isinstance(node.value, ast.BinOp):
            visitor = BinaryOpToAssign()
            assign = visitor.visit(node.value)
            #node.value = assign.targets[0]
            node.value = ast.Name(id = assign.targets[0].id, ctx = ast.Load())
            return visitor.stmts + [node]
        elif isinstance(node.value, ast.Call):
            visitor = BinaryOpToAssign()
            newargs = [visitor.visit(arg) for arg in node.value.args]
            node.value.args = []
            for newargs in newargs:
                if isinstance(newargs, ast.Assign):
                    node.value.args.append(ast.Name(id = newargs.targets[0].id, ctx = ast.Load()))
                else:
                    node.value.args.append(newargs)
            return visitor.stmts + [node]
        elif isinstance(node.value, ast.Tuple):
            visitor = BinaryOpToAssign()
            newelts = [visitor.visit(arg) for arg in node.value.elts]
            node.value.elts = []
            for newelt in newelts:
                if isinstance(newelt, ast.Assign):
                    node.value.elts.append(ast.Name(id = newelt.targets[0].id, ctx = ast.Load()))
                else:
                    node.value.elts.append(newelt)
            return visitor.stmts + [node]
        else:
            return node

class ReturnExprToStmt(ast.NodeTransformer):
    def visit_Return(self, node):
        if not isinstance(node.value, ast.Name):
            assign = ast.Assign(targets = [ast.Name(id = '__ret', ctx = ast.Store())], value = node.value, lineno = node.lineno, col_offset = node.col_offset)
            node.value = ast.Name(id = '__ret', ctx = ast.Load())
            return [assign] + [node]
        else:
            return node


class RemoveRedundantAssign(ast.NodeTransformer):
    def __init__(self):
        self.prev = None

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Name) and node.value.id.startswith('__v'):
            assert self.prev != None and self.prev.targets[0].id == node.value.id
            self.prev.targets[0] = node.targets[0]
            return
        else:
            self.prev = node
            return node


def transform(tree, **kwargs):
    tree = ReturnExprToStmt().visit(tree)
    tree = ToSingleOperatorStmts().visit(tree)
    tree = RemoveRedundantAssign().visit(tree)
    return tree
