from os import mkdir
from sys import pycache_prefix, implementation
from os.path import exists, join, dirname, splitext
from importlib.machinery import BYTECODE_SUFFIXES
from marshal import dump, load
from .version import version
from .prep import mtime_it


__all__ = 'CACHE_DIR_PATH', 'MARSHAL_VERSION', 'VERSION_TAG', 'CACHE_EXT', \
          'pkg_cache_path', 'create_cache_dir', 'dump_cache', 'load_cache'
CACHE_DIR_PATH = pycache_prefix or '__pycache__'
MARSHAL_VERSION = 4
VERSION_TAG = implementation.cache_tag.split('-')[1]  # e.g: 'cpython-312' to '312'
CACHE_EXT = BYTECODE_SUFFIXES[0]  # e.g: ['.pyc'] to '.pyc'


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
    '''
    name = splitext(file_name)[0]  # '__init__.py' to '__init__'
    new_file_name = f'{name}.{func_name}-{VERSION_TAG}{CACHE_EXT}'  # '__init__.importer-312.pyc'
    return join(pkg_path, CACHE_DIR_PATH, new_file_name)


def create_cache_dir(cache_path):
    ''' Create `__pycache__` directory

        Type:
            cache_path: str
            return:     None

        Example
            >>> create_cache_dir('/path/pkg/__pycache__/__init__.importer-312.pyc')
    '''
    pkg_dir = dirname(cache_path)
    if not exists(pkg_dir):
        mkdir(pkg_dir)  # create `__pycache__` if it doesn't exist!
        return True


def dump_cache(cache_path, data, recursive, exclude_file, exclude_dir, dir_mtime):
    ''' Create cached file

        Type
            cache_path:   str
            data:         any
            recursive:    bool
            exclude_file: List[str]
            exclude_dir:  List[str]
            dir_mtime:    Dict[str, float]
            return:       None

        Example
            >>> dump_cache('/path/pkg/__pycache__/__init__.importer-312', ...)
    '''
    with open(cache_path, 'w+b') as file:
        dump((version, recursive, exclude_file, exclude_dir, dir_mtime, data), file, MARSHAL_VERSION)


def load_cache(cache_path, recursive, exclude_file, exclude_dir):
    ''' Load cached file

        Type
            cache_path:   str
            recursive:    bool
            exclude_file: List[str]
            exclude_dir:  List[str]
            return:       any

        Example
            >>> load_cache('/path/pkg/__pycache__/__init__.importer-312.pyc')
    '''
    with open(cache_path, 'rb') as file:
        try:
            cached_version, cached_recursive, cached_exclude_file, cached_exclude_dir, dir_mtime, data = load(file)
        except Exception:
            return None

        # check if Dynamic Import version has changed!
        if version != cached_version:
            return None
        elif recursive != cached_recursive:
            # check if `recursive` has changed!')
            return None
        elif exclude_file != cached_exclude_file:
            # check if `exclude_file` has changed!
            return None
        elif exclude_dir != cached_exclude_dir:
            # check if `exclude_dir` has changed!
            return None
        else:
            # check if dir has changed.
            for dir_path, mtime in dir_mtime.items():
                if mtime != mtime_it(dir_path):
                    return None
            # check if each of the the files have changed.
            for _, file_path, _, mtime in data.values():
                if mtime != mtime_it(file_path):
                    return None
        return data
