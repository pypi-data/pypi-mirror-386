import ast
import textwrap
import ast_transforms as at

def test_get_used_names():
    code = """
    for i in range(N):
        c[i] = a[i] + b[i]
    """
    tree = ast.parse(textwrap.dedent(code))
    names = at.get_used_names(tree, no_funcname=False)
    assert sorted(names) == sorted(['N', 'i', 'range', 'c', 'a', 'b'])

    names = at.get_used_names(tree, no_funcname=True)
    assert sorted(names) == sorted(['N', 'i', 'c', 'a', 'b'])
