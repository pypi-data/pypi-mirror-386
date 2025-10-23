def add_func_decorator(tree, decorator):
    """
    Adds a decorator to all functions in the AST.

    Parameters
    ----------
    tree : ast.AST
        The AST of the Python code to transform.
    decorator : str
        The decorator to add. Can be a fully-qualified name
        (e.g., "numba.jit") or a simple name (e.g., "jit").

    Returns
    -------
    ast.AST
        The transformed AST.
    """
    from .passes import add_func_decorator as m
    return m.transform(tree, decorator)

def remove_func_decorator(tree):
    """
    Remove all decorators from functions in the AST.

    Parameters
    ----------
    tree : ast.AST
        The AST of the Python code to transform.

    Returns
    -------
    ast.AST
        The transformed AST.
    """
    from .passes import remove_func_decorator as m
    return m.transform(tree)

def get_used_names(tree, no_funcname=True):
    '''
    Return a sorted list of all names used in the AST.

    Parameters
    ----------
    tree : ast.AST
        The AST of the Python code to analyze.
    no_funcname : bool, optional
        If True, function names are excluded from the result. Default is True.

    Returns
    -------
    list of str
        The sorted list of used names.
    '''
    from .passes import get_used_names as m
    return m.analyze(tree, no_funcname)

def hoist_shape_attr(tree):
    '''
    Hoists shape attribute accesses in the AST. For example, 
    `a.shape[0]` is replaced with `a_shape_0`, and an assignment
    `a_shape_0 = a.shape[0]` is inserted before the loop.

    Parameters
    ----------
    tree : ast.AST
        The AST of the Python code to transform.

    Returns
    -------
    ast.AST
        The transformed AST.
    '''
    from .passes import hoist_shape_attr as m
    return m.transform(tree)