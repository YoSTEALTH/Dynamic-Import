from ast import (
    Add,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    AugAssign,
    ClassDef,
    FunctionDef,
    List,
    Name,
    Tuple,
    literal_eval,
    parse,
)
from importlib import import_module


__all__ = 'extract_variable', 'extract_so_variable'
LIST_TUPLE = (list, tuple)
DEFINITION = (FunctionDef, AsyncFunctionDef, ClassDef)
UNPACK = (Tuple, List)


def all_value(node, path):
    ''' Evaluate the literal assigned to `__all__`

        Type
            node:   ast.expr
            path:   str
            return: list[str] | tuple[str]
    '''
    try:
        value = literal_eval(node)
    except ValueError:
        raise ValueError(f'`__all__` in {path!r} must be a literal list, tuple or string!') from None

    if type(value) is str:
        return (value,)
    elif type(value) in LIST_TUPLE and all(type(each) is str for each in value):
        return value
    raise TypeError(f'`__all__` values in {path!r} is not string!')


def extract_variable(path):
    ''' Extract variable value from source file

        Type
            path:   str
            return: list[str] | tuple[str]

        Example
            # ./file_1.py
            # __all__ = ('one', 'two', 'three')
            >>> extract_variable('file_1.py')
            ('one', 'two', 'three')

            # ./file_2.py
            # __all__ = 'one'
            >>> extract_variable('file_2.py')
            ('one',)

            # ./file_3.py
            # `__all__` is not defined.
            >>> extract_variable('file_3.py')
            ('variable', 'ClassName', 'function_name', 'DEFINE')

        Note
            - `__all__` must be a literal `list`, `tuple` or `str`; `__all__ += [...]` is supported.
            - without `__all__` every module-level `name = ...`, `name: type = ...`, `a, b = ...`,
              `def`, `async def` and `class` is collected. Attribute and subscript assignments
              (`obj.attr = 1`, `d['key'] = 1`) do not define a module name and are skipped.
            - without `__all__` a name starting with `_` is private and not collected, like `from mod import *`.
            - only top-level statements are scanned: names defined inside `if`, `try`, `with`,
              `for`, ... blocks are not found. List them in `__all__` instead.
    '''
    with open(path, 'rb') as file:
        content = file.read()

    variables = []
    found = None  # value of `__all__` if defined
    for body in parse(content, path).body:
        node = body.__class__
        if node is Assign:
            for target in body.targets:
                if target.__class__ is Name:
                    if target.id == '__all__':
                        found = all_value(body.value, path)
                    else:
                        variables.append(target.id)
                elif target.__class__ in UNPACK:  # e.g: `x, y = 1, 2`
                    variables.extend(elt.id for elt in target.elts if elt.__class__ is Name)
        elif node is AnnAssign:  # e.g: `x: int = 1`
            if body.value is not None and body.target.__class__ is Name:
                if body.target.id == '__all__':
                    found = all_value(body.value, path)
                else:
                    variables.append(body.target.id)
        elif node is AugAssign:  # e.g: `__all__ += ['x']`
            if body.target.__class__ is Name and body.target.id == '__all__' and body.op.__class__ is Add:
                value = all_value(body.value, path)
                found = value if found is None else type(found)((*found, *value))
        elif node in DEFINITION:
            variables.append(body.name)
    if found is None:
        return [i for i in variables if i[0] != '_']  # like `from mod import *` without `__all__`
    return found


def extract_so_variable(module_name):
    ''' Extract variable value from `.so` cython generated file

        Type
            module_name: str
            return:      list[str] | tuple[str]

        Example
            # /path/pkg/file_1.cpython-312-x86_64-linux-gnu.so
            # __all__ = ('one', 'two', 'three')

            >>> extract_so_variable('pkg.file_1', '__all__')
            ['one', 'two', 'three']

            # /path/pkg/file_2.cpython-312-x86_64-linux-gnu.so
            # __all__ = 'one'
            >>> extract_so_variable('pkg.file_2', '__all__')
            ['one']

            # /path/pkg/file_3.cpython-312-x86_64-linux-gnu.so
            # `__all__` is not defined.
            >>> extract_so_variable('pkg.file_3', '__all__')
            ['variable', 'ClassName', 'function_name']

        Note
            - without `__all__` a name starting with `_` is private and not collected, like `from mod import *`.
    '''
    module = import_module(module_name)
    # note: `import_module` loads `.so` file and gets the list of names. Currently there
    #       isn't a better solution that I know of.

    variables = []
    if find := getattr(module, '__all__', None):
        _type = type(find)
        if _type in LIST_TUPLE:
            variables.extend(find)
        elif _type is str:
            variables.append(find)
        else:
            raise TypeError(f'can not parse `__all__` value in {module_name!r}')
    else:
        variables.extend(i for i in dir(module) if i[0] != '_')  # like `from mod import *` without `__all__`
    return variables
