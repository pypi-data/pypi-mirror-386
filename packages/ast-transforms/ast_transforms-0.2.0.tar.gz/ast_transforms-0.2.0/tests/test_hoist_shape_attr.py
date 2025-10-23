import ast
import textwrap
import ast_transforms as at

def test_hoist_shape_attr():
    code = """
    for i in range(a.shape[0]):
        x = a.shape[0] + b.shape[1]
        y = a[i] + b[i]
    """
    expected = """
    a_shape_0 = a.shape[0]
    b_shape_1 = b.shape[1]
    for i in range(a_shape_0):        
        x = a_shape_0 + b_shape_1
        y = a[i] + b[i]
    """
    tree = ast.parse(textwrap.dedent(code))
    tree = at.hoist_shape_attr(tree)
    assert ast.dump(tree) == ast.dump(ast.parse(textwrap.dedent(expected)))

