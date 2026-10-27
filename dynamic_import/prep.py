from importlib.machinery import EXTENSION_SUFFIXES
from os import sep, stat, walk
from os.path import join
from .special import special


__all__ = 'EXT_SUFFIX', 'prep_package', 'load_rank', 'prep_files', 'prep_variables', 'is_extension'
# e.g: ('.py', '.cpython-312-x86_64-linux-gnu.so', '.abi3.so', '.so'), Windows: ('.py', '.cp312-win_amd64.pyd', '.pyd')
EXT_SUFFIX = ('.py', *EXTENSION_SUFFIXES)
# note: plain `.so` is also used by every shared library bundled with a package (`libfoo.so`), so an
#       untagged `.so` is only scanned if `is_extension()` finds its init function (`liburing.so`).
TAGGED = tuple(i for i in EXTENSION_SUFFIXES if i != '.so')  # e.g: ('.cpython-312-x86_64-linux-gnu.so', ...)
LOAD_ORDER = (*EXTENSION_SUFFIXES, '.py')  # `import` tries extension modules before source, in this order


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
    from mmap import ACCESS_READ, mmap  # only needed to scan, not on a cache hit
    tail = unicode + b'_' + symbol + b'\0'  # e.g: b'_liburing\0', one pass over the file for both hooks
    with open(file_path, 'rb') as file, mmap(file.fileno(), 0, access=ACCESS_READ) as data:
        at = data.find(tail)
        while at != -1:
            if data[max(at - 6, 0):at] == b'PyInit' or data[max(at - 11, 0):at] == b'PyModExport':
                return True
            at = data.find(tail, at + 1)
    return False


def prep_package(pkg_name, pkg_path, recursive, exclude_file, exclude_dir):
    '''
        Type
            pkg_name:     str
            pkg_path:     str
            recursive:    bool
            exclude_file: list[str]
            exclude_dir:  list[str]
            return:       tuple[dict[str, tuple[str, str, tuple[str], float]], dict[str, float]]

        Example
            >>> prep_package('pkg', 'path/pkg/', True, [], [])
            {'one': ('pkg.module', 'pkg/module.py', ('one', ...), 123.45), ...}, {'pkg/': 123.45, ...}

        Note
            - raises `ImportError` if two modules export the same name.
            - one module found as both `mod.py` and `mod.<tag>.so` keeps the file `import` would load (the `.so`).
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
            if (other := info.get(var)) is not None:
                if other[0] != module:
                    error = f'`importer()` found name {var!r} in both {other[1]!r} and {file_path!r}, ' \
                            'exported names must be unique (use `__all__` to choose what a module exports).'
                    raise ImportError(error, name=pkg_name, path=file_path)
                if load_rank(other[1]) < load_rank(file_path):
                    continue  # same module, `import` would load the other file
            info[var] = (module, file_path, variables, mtime)
    return info, dir_mtime


def load_rank(file_path):
    ''' Position of the file's suffix in `import` order, lower is loaded first

        Type
            file_path: str
            return:    int

        Example
            >>> load_rank('/path/pkg/mod.cpython-312-x86_64-linux-gnu.so') < load_rank('/path/pkg/mod.py')
            True
    '''
    return next(i for i, suffix in enumerate(LOAD_ORDER) if file_path.endswith(suffix))


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
            - `__pycache__`, `exclude_dir` and dotted (`name.dSYM`, `.git`) directories are not descended into.
            - directories and files are visited in sorted order, the same on every machine.
            - an untagged `.so` that is not an extension module (`libfoo.so`) is skipped, see `is_extension()`.
    '''
    skip = len(pkg_path) - len(pkg_name) - 1  # "/path/pkg" - "pkg" - 1
    for root, dirs, files in walk(pkg_path):
        root_path = join(root, '')  # '/path/pkg/sub' to '/path/pkg/sub/'
        # do not descend into `__pycache__`, excluded directories, or a name with a `.` (e.g: macOS
        # 'mod.cpython-312-darwin.so.dSYM' debug bundle): `import` splits on dots, so it is never a package.
        # sorted: `walk()` gives file-system order, the cache and `dir(pkg)` must not depend on it.
        dirs[:] = sorted(d for d in dirs
                         if d != '__pycache__' and '.' not in d and join(root_path, d, '') not in exclude_dir)
        files.sort()
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
            yield:       tuple[str, tuple[str]]
            return:      None

        Example
            >>> for var, variables in prep_variables('pkg.sub.module', '/path/pkg/sub/module.py')
            ...     var, variables
            'one', ('one', 'two')
            'two', ('one', 'two')
    '''
    from .extract import extract_so_variable, extract_variable  # `ast`: only needed to scan, not on a cache hit

    if file_path.endswith(EXT_SUFFIX[0]):  # .py
        variables = extract_variable(file_path)
    else:  # .so, `prep_files()` only yields `EXT_SUFFIX` files
        variables = extract_so_variable(module_name)

    variables = tuple(special(variables))  # special names are never exported, `Module` relies on it
    for var in variables:
        yield var, variables  # e.g. 'one', ('one', 'two')
