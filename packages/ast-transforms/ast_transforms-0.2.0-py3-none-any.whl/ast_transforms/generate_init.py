import pkgutil
from pathlib import Path

body = ""
for modinfo in pkgutil.iter_modules([f'{Path(__file__).parent}/passes']):
    name = modinfo.name
    body += f"def {name}(tree, *args):\n"
    body += f"    '''Apply the `{name}` AST transform.'''\n"
    body += f"    from .passes import {name} as m\n"
    body += f"    return m.transform(tree, *args)\n"
    body += "\n"

Path(f'{Path(__file__).parent}/__init__.py').write_text(body)