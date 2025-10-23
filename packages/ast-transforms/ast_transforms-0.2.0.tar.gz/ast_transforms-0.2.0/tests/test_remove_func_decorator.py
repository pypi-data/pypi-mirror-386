import ast
import textwrap
import ast_transforms as at

def test_remove_func_decorator_simple():
    code = """
    @decorator
    def foo():
        return 42
    """
    tree = ast.parse(textwrap.dedent(code))
    new_tree = at.remove_func_decorator(tree)
    new_code = ast.unparse(new_tree)

    expected = """
    def foo():
        return 42
    """
    # Normalize whitespace for comparison
    assert new_code == ast.unparse(ast.parse(textwrap.dedent(expected)))
