# AST Transforms

A collection of AST-based Python transformations for manipulating code programmatically.

## Installation

```bash
pip install ast_transforms
```

## Usage

```python
import ast
import ast_transforms as at

code = '''
@mydecorator
def foo():
    print("foo")
'''

# Parse code into an AST
tree = ast.parse(code)

# Apply transformations
tree = at.remove_func_decorator(tree)  # removes all function decorators

# Convert AST back to source code
new_code = ast.unparse(tree)
print(new_code)
```

**Output:**

```python
def foo():
    print("foo")
```

---

## Passes

* `remove_func_decorator(tree)` – removes all decorators from functions.
* More passes are to be added ...
