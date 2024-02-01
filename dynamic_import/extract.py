from importlib import import_module
from ast import FunctionDef, AsyncFunctionDef, ClassDef, Assign, parse, literal_eval
from .special import special


__all__ = 'extract_variable', 'extract_so_variable'
LIST_TUPLE = (list, tuple)


def extract_variable(path):
    ''' Extract variable value from source file

        Type
            path:   str
            return: Union[List[str], Tuple[str]

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
    '''
    with open(path, 'rb') as file:
        content = file.read()

    variables = []
    for body in parse(content, path).body:
        if body.__class__ is Assign:
            name = body.targets[0].id
            if name == '__all__':
                value = literal_eval(body.value)
                _type = type(value)
                if _type in LIST_TUPLE:
                    return value
                elif _type is str:
                    return (value,)
                else:
                    raise TypeError(f'`__all__` values in {path!r} is not string!')
            variables.append(name)
        elif body.__class__ in (FunctionDef, AsyncFunctionDef, ClassDef):
            variables.append(body.name)
    return variables


def extract_so_variable(module_name):
    ''' Extract variable value from `.so` cython generated file

        Type
            module_name: str
            return:      Union[List[str], Tuple[str]

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
        for var in special(dir(module)):
            variables.append(var)
    return variables
