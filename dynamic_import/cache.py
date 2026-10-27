import sys
from importlib.machinery import BYTECODE_SUFFIXES
from marshal import dump, load
from os import altsep, getpid, makedirs, remove, replace, sep, stat
from os.path import dirname, join, splitext


__all__ = 'CACHE_DIR_PATH', 'MARSHAL_VERSION', 'VERSION_TAG', 'CACHE_EXT', \
          'pkg_cache_path', 'create_cache_dir', 'dump_cache', 'load_cache'
CACHE_DIR_PATH = '__pycache__'
MARSHAL_VERSION = 4
VERSION_TAG = sys.implementation.cache_tag.split('-')[1]  # e.g: 'cpython-312' to '312'
CACHE_EXT = BYTECODE_SUFFIXES[0]  # e.g: ['.pyc'] to '.pyc'
SEPARATORS = sep + (altsep or '')  # '/', Windows: '\/'


def pkg_cache_path(pkg_path, file_name, func_name):
    ''' Temp cached file path pattern

        Type
            pkg_path:  str
            file_name: str
            func_name: str
            return:    str

        Example
            >>> pkg_cache_path('/path/pkg/', '__init__.py', 'importer')
            '/path/pkg/__pycache__/__init__.importer-312.pyc'

            # with `sys.pycache_prefix = '/tmp/pyc'` (or `PYTHONPYCACHEPREFIX`)
            >>> pkg_cache_path('/path/pkg/', '__init__.py', 'importer')
            '/tmp/pyc/path/pkg/__init__.importer-312.pyc'

        Note
            - mirrors CPython: with `sys.pycache_prefix` set the absolute package path is
              appended to the prefix, so each package still gets its own cache file.
    '''
    name = splitext(file_name)[0]  # '__init__.py' to '__init__'
    new_file_name = f'{name}.{func_name}-{VERSION_TAG}{CACHE_EXT}'  # '__init__.importer-312.pyc'
    if prefix := sys.pycache_prefix:
        if pkg_path[1:2] == ':' and pkg_path[0:1] not in SEPARATORS:
            pkg_path = pkg_path[2:]  # Windows: 'C:\path\pkg\' to '\path\pkg\', like `cache_from_source()`
        return join(prefix, pkg_path.lstrip(SEPARATORS), new_file_name)
    return join(pkg_path, CACHE_DIR_PATH, new_file_name)


def create_cache_dir(cache_path):
    ''' Create `__pycache__` directory

        Type:
            cache_path: str
            return:     None

        Example
            >>> create_cache_dir('/path/pkg/__pycache__/__init__.importer-312.pyc')
    '''
    makedirs(dirname(cache_path), exist_ok=True)  # `exist_ok`: already there, or another process won the race.


def dump_cache(cache_path, data, recursive, exclude_file, exclude_dir, dir_mtime, version):
    ''' Create cached file

        Type
            cache_path:   str
            data:         any
            recursive:    bool
            exclude_file: list[str]
            exclude_dir:  list[str]
            dir_mtime:    dict[str, float]
            version:      str
            return:       None

        Example
            >>> dump_cache('/path/pkg/__pycache__/__init__.importer-312', ...)

        Note
            - written to a temporary file that then replaces `cache_path` (like CPython's `_write_atomic()`),
              so another process starting at the same time never reads a half-written cache.
    '''
    tmp_path = f'{cache_path}.{getpid()}.tmp'
    try:
        with open(tmp_path, 'wb') as file:
            dump((version, recursive, exclude_file, exclude_dir, dir_mtime, data), file, MARSHAL_VERSION)
        replace(tmp_path, cache_path)
    except BaseException:
        try:
            remove(tmp_path)
        except OSError:
            pass
        raise


def load_cache(cache_path, recursive, exclude_file, exclude_dir, version):
    ''' Load cached file

        Type
            cache_path:   str
            recursive:    bool
            exclude_file: list[str]
            exclude_dir:  list[str]
            version:      str
            return:       any

        Example
            >>> load_cache('/path/pkg/__pycache__/__init__.importer-312.pyc')
    '''
    try:
        with open(cache_path, 'rb') as file:
            cached_version, cached_recursive, cached_exclude_file, cached_exclude_dir, dir_mtime, data = load(file)

            if version != cached_version:
                return None  # check if Dynamic Import version has changed!
            elif recursive != cached_recursive:
                return None  # check if `recursive` has changed!'
            elif exclude_file != cached_exclude_file:
                return None  # check if `exclude_file` has changed!
            elif exclude_dir != cached_exclude_dir:
                return None  # check if `exclude_dir` has changed!
            else:
                # check if dir has changed.
                for dir_path, mtime in dir_mtime.items():
                    if mtime != stat(dir_path).st_mtime:
                        return None
                # check if each of the the files have changed.
                for _, file_path, _, mtime in data.values():
                    if mtime != stat(file_path).st_mtime:
                        return None
            return data
    except Exception:
        return None
