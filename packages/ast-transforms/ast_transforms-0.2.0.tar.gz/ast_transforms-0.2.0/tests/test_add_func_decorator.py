import ast
import textwrap
import ast_transforms as at

def test_add_func_decorator_simple():
    code = """
    def foo():
        return 42
    """
    tree = ast.parse(textwrap.dedent(code))
    new_tree = at.add_func_decorator(tree, "jit")
    new_code = ast.unparse(new_tree)

    expected = """
    @jit
    def foo():
        return 42
    """
    assert new_code == ast.unparse(ast.parse(textwrap.dedent(expected)))
