from os import walk, stat
from os.path import join, dirname
try:
    from functools import cache
except ImportError:  # account for python 3.8
    from functools import lru_cache as cache
from importlib.machinery import EXTENSION_SUFFIXES
from .extract import extract_variable, extract_so_variable
from .special import special


__all__ = 'EXT_SUFFIX', 'prep_package', 'prep_files', 'prep_variables', 'mtime_it'
# e.g: ('.py', '.cpython-312-x86_64-linux-gnu.so', '.abi3.so')
EXT_SUFFIX = ('.py', *(i for i in EXTENSION_SUFFIXES if i != '.so'))


def prep_package(pkg_file, recursive):
    '''
        Type
            pkg_file:  str
            recursive: bool
            return:    Dict[str, Tuple[str, stf, Union[List[str], Tuple[str]]]]

        Example
            >>> prep_package('package', True)
            {'one': ('sub.module', '/path/pkg/sub/module.py', ('one', 'two', 'three', ...)), ...}
    '''
    info = {}
    dir_mtime = {}
    for name, file_path, mtime in prep_files(pkg_file, recursive, dir_mtime):
        # print('name:', name, 'file_path:', file_path)
        for var, variables in prep_variables(file_path, name):
            info[var] = (name, file_path, variables, mtime)
    # print('dir_mtime:', dir_mtime)
    return info, dir_mtime


def prep_files(pkg_file, recursive, dir_mtime):
    ''' Prepare python files and module names

        Type
            pkg_file:  str
            recursive: bool
            yield:     Tuple[str, Union[Tuple[str], List[str]], float]
            return:    None

        Example
            >>> for name, file_path in prep_files('pkg', /path/pkg'):
            ...     name, file_path
            ('sub.module', '/path/pkg/sub/module.py', 123.45)
            ...

        Note
            - Any sub-directories with `__init__.py` file found is ignored!!!
            as there should only be 1  `__init__.py` file at top level.
    '''
    # note: using `pkg_file` to avoid cases where package & pkg_path was overridden by user
    # its assumed `pkg_file` ends with `__init__.py` why there is no check here

    pkg_path = dirname(pkg_file)  # e.g: `/path/pkg`
    skip = len(pkg_path)
    package = pkg_path.split('/')[-1]  # e.g. `pkg`
    for root, dirs, files in walk(pkg_path):
        if root.endswith('/__pycache__'):
            continue
        if files:
            sub = '.'.join(root[skip:].split('/'))  # e.g: `/path/pkg/sub` -to-> `.sub`
            for file in files:
                if file.endswith(EXT_SUFFIX):
                    # only add directory that have `EXT_SUFFIX` in it.
                    dir_mtime[root] = mtime_it(root)
                    file_path = join(root, file)
                    mtime = stat(file_path).st_mtime
                    if file == '__init__.py':
                        yield f'{package}{sub}', file_path, mtime
                    else:
                        yield f'{package}{sub}.{file.split(".")[0]}', file_path, mtime
                        # ('pkg.sub.module', '/path/pkg/sub/module.py')
                        # ('pkg.sub.module', '/path/pkg/sub/module.cpython-312-x86_64-linux-gnu.so')
        if not recursive:
            break


@cache
def mtime_it(root):
    return stat(root).st_mtime


def prep_variables(file_path, module_name):
    ''' Prepare `__all__` variable names

        Type
            file_path:   str
            module_name: str
            yield:       Tuple[str, Union[List[str], Tuple[str]]]
            return:      None

        Example
            >>> for var, variables in prep_variables('/path/pkg/sub/module.py')
            ...     var, variables
            'one', ('one', 'two')
            'two', ('one', 'two')
    '''
    if file_path.endswith(EXT_SUFFIX[0]):  # .py
        variables = extract_variable(file_path)
    elif file_path.endswith(EXT_SUFFIX[1]):  # .so
        variables = extract_so_variable(module_name)
    else:
        return None

    for var in special(variables, error=True):
        yield var, variables  # e.g. 'one', ('one', 'two')
