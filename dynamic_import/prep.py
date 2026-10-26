from os import walk, stat
from os.path import join
from importlib.machinery import EXTENSION_SUFFIXES
from .extract import extract_variable, extract_so_variable
from .special import special


__all__ = 'EXT_SUFFIX', 'prep_package', 'prep_files', 'prep_variables'
# e.g: ('.py', '.cpython-312-x86_64-linux-gnu.so', '.abi3.so')
EXT_SUFFIX = ('.py', *(i for i in EXTENSION_SUFFIXES if i != '.so'))
# note: plain `.so` is left out on purpose. Every shared library bundled with a package (`libfoo.so`)
#       would otherwise be `import_module`'d during the scan and fail the whole package. Extension
#       modules built by setuptools/cython always carry the tagged suffix.


def prep_package(pkg_name, pkg_path, recursive, exclude_file, exclude_dir):
    '''
        Type
            pkg_name:     str
            pkg_path:     str
            recursive:    bool
            exclude_file: list[str]
            exclude_dir:  list[str]
            return:     tuple[dict[str, tuple[str, str, list[str] | tuple[str], float]], dict[str, float]]

        Example
            >>> prep_package('pkg', 'path/pkg/', True, [], [])
            {'one': ('pkg.module', 'pkg/module.py', ('one', ...), 123.45), ...}, {'pkg/': 123.45, ...}
    '''
    info = {}
    dir_mtime = {}
    for module, file_path, mtime in prep_files(pkg_name,
                                               pkg_path,
                                               recursive,
                                               dir_mtime,
                                               exclude_file,
                                               exclude_dir):
        for var, variables in prep_variables(module, file_path):
            info[var] = (module, file_path, variables, mtime)
    return info, dir_mtime


def prep_files(pkg_name, pkg_path, recursive, dir_mtime, exclude_file, exclude_dir):
    ''' Prepare python files and module names

        Type
            pkg_name:     str
            pkg_path:     str
            recursive:    bool
            dir_mtime:    dict[str, float]
            exclude_file: list[str]
            exclude_dir:  list[str]
            yield:        tuple[str, tuple[str] | list[str], float]
            return:       None

        Example
            >>> for name, file_path, mtime in prep_files('pkg', /path/pkg'):
            ...     name, file_path, mtime
            'sub.module' '/path/pkg/sub/module.py' 123.45

        Note
            - every scanned directory is recorded in `dir_mtime` (even ones without a module yet),
              so a module added to a data-only directory later still invalidates the cache.
            - `__pycache__` and `exclude_dir` directories are not descended into.
    '''
    skip = len(pkg_path) - len(pkg_name) - 1  # "/path/pkg" - "pkg" - 1
    for root, dirs, files in walk(pkg_path):
        root_path = root if root.endswith('/') else f'{root}/'
        # do not descend into `__pycache__` or excluded directories.
        dirs[:] = [d for d in dirs if d != '__pycache__' and f'{root_path}{d}/' not in exclude_dir]
        dir_mtime[root_path] = stat(root_path).st_mtime  # a new file in this directory changes it

        if files:
            # e.g: "/path/pkg/sub/module/" to "pkg.sub.module"
            if (module_name := root[skip:].replace("/", ".")).endswith('.'):
                module_name = module_name[:-1]

            for file in files:
                if file.endswith(EXT_SUFFIX):
                    # skip excluded file
                    if (file_path := join(root, file)) in exclude_file:
                        continue
                    mtime = stat(file_path).st_mtime

                    if file == '__init__.py':
                        yield f'{module_name}', file_path, mtime
                    else:
                        yield f'{module_name}.{file.split(".")[0]}', file_path, mtime
                        # ('pkg.sub.module', '/pkg/sub/module.py', 123.45)
                        # ('pkg.sub.module', '/pkg/sub/module*.so', 123.45)
        if not recursive:
            break


def prep_variables(module_name, file_path):
    ''' Prepare `__all__` variable names

        Type
            module_name: str
            file_path:   str
            yield:       tuple[str, list[str] | tuple[str]]
            return:      None

        Example
            >>> for var, variables in prep_variables('pkg.sub.module', '/path/pkg/sub/module.py')
            ...     var, variables
            'one', ('one', 'two')
            'two', ('one', 'two')
    '''
    if file_path.endswith(EXT_SUFFIX[0]):  # .py
        variables = extract_variable(file_path)
    elif file_path.endswith(EXT_SUFFIX[1:]):  # .so
        variables = extract_so_variable(module_name)
    else:
        return None

    for var in special(variables):
        yield var, variables  # e.g. 'one', ('one', 'two')
