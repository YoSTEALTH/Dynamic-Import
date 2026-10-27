from importlib.machinery import EXTENSION_SUFFIXES
from mmap import ACCESS_READ, mmap
from os import sep, stat, walk
from os.path import join
from .extract import extract_so_variable, extract_variable
from .special import special


__all__ = 'EXT_SUFFIX', 'prep_package', 'prep_files', 'prep_variables', 'is_extension'
# e.g: ('.py', '.cpython-312-x86_64-linux-gnu.so', '.abi3.so', '.so'), Windows: ('.py', '.cp312-win_amd64.pyd', '.pyd')
EXT_SUFFIX = ('.py', *EXTENSION_SUFFIXES)
# note: plain `.so` is also used by every shared library bundled with a package (`libfoo.so`), so an
#       untagged `.so` is only scanned if `is_extension()` finds its init function (`liburing.so`).
TAGGED = tuple(i for i in EXTENSION_SUFFIXES if i != '.so')  # e.g: ('.cpython-312-x86_64-linux-gnu.so', ...)


def is_extension(file_path, name):
    ''' Is the untagged `.so` file a Python extension module?

        Type
            file_path: str
            name:      str    module base name, e.g: 'liburing'
            return:    bool

        Example
            >>> is_extension('/path/pkg/liburing.so', 'liburing')
            True
            >>> is_extension('/path/pkg/libfoo.so', 'libfoo')  # plain shared library
            False

        Note
            - looks for the exported symbol name the import system calls, `PyInit_<name>` (3.15+ also
              `PyModExport_<name>`), in the file. The file is never loaded, so a plain library is not run.
            - a non-ASCII name uses the `PyInitU_<punycode>` form, like the import system does.
    '''
    if name.isascii():
        symbol, unicode = name.encode(), b''
    else:
        symbol, unicode = name.encode('punycode').replace(b'-', b'_'), b'U'
    if not stat(file_path).st_size:
        return False  # `mmap` can not map an empty file
    with open(file_path, 'rb') as file, mmap(file.fileno(), 0, access=ACCESS_READ) as data:
        return any(data.find(hook + unicode + b'_' + symbol + b'\0') != -1 for hook in (b'PyInit', b'PyModExport'))


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
            - an untagged `.so` that is not an extension module (`libfoo.so`) is skipped, see `is_extension()`.
    '''
    skip = len(pkg_path) - len(pkg_name) - 1  # "/path/pkg" - "pkg" - 1
    for root, dirs, files in walk(pkg_path):
        root_path = join(root, '')  # '/path/pkg/sub' to '/path/pkg/sub/'
        # do not descend into `__pycache__` or excluded directories.
        dirs[:] = [d for d in dirs if d != '__pycache__' and join(root_path, d, '') not in exclude_dir]
        dir_mtime[root_path] = stat(root_path).st_mtime  # a new file in this directory changes it

        if files:
            # e.g: "/path/pkg/sub/module/" to "pkg.sub.module"
            if (module_name := root[skip:].replace(sep, '.')).endswith('.'):
                module_name = module_name[:-1]

            for file in files:
                if file.endswith(EXT_SUFFIX):
                    # skip excluded file
                    if (file_path := join(root, file)) in exclude_file:
                        continue
                    name = file.split('.')[0]
                    # skip plain shared library e.g: 'libfoo.so'
                    if file.endswith('.so') and not file.endswith(TAGGED) and not is_extension(file_path, name):
                        continue
                    mtime = stat(file_path).st_mtime

                    if file == '__init__.py':
                        yield f'{module_name}', file_path, mtime
                    else:
                        yield f'{module_name}.{name}', file_path, mtime
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
