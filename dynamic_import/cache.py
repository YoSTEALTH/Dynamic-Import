from os import mkdir
from sys import pycache_prefix, implementation
from os.path import exists, join, dirname, splitext, basename
from importlib.machinery import BYTECODE_SUFFIXES
from marshal import dump, load
from .version import version
from .prep import mtime_it


__all__ = 'CACHE_DIR_PATH', 'MARSHAL_VERSION', 'VERSION_TAG', 'CACHE_EXT', 'pkg_cache_path', \
          'dump_cache', 'load_cache', 'create_cache_dir'
CACHE_DIR_PATH = pycache_prefix or '__pycache__'
MARSHAL_VERSION = 4
VERSION_TAG = implementation.cache_tag.split('-')[1]  # e.g: 'cpython-312' to '312'
CACHE_EXT = BYTECODE_SUFFIXES[0]  # e.g: ['.pyc'] to '.pyc'


def pkg_cache_path(pkg_file, name):
    ''' Temp cached file path pattern

        Type
            pkg_file: str
            name:     str
            return:   str

        Example
            >>> pkg_cache_path('/path/pkg/__init__.py')
            '/path/pkg/__pycache__/__init__.dynamic-import.pyc'
    '''
    file_name = f'{splitext(basename(pkg_file))[0]}.{name}-{VERSION_TAG}{CACHE_EXT}'
    return join(dirname(pkg_file), CACHE_DIR_PATH, file_name)


def create_cache_dir(cache_path):
    ''' Create `__pycache__` directory

        Type:
            cache_path: str
            return:     None

        Example
            >>> create_cache_dir('/path/pkg/__pycache__/__init__.dynamic-import.pyc')
    '''
    pkg_dir = dirname(cache_path)
    if not exists(pkg_dir):
        mkdir(pkg_dir)  # create `__pycache__` if it doesn't exist!
        return True


def dump_cache(cache_path, data, recursive, exclude_paths, dir_mtime):
    ''' Create cached file

        Type
            cache_path:    str
            data:          any
            recursive:     bool
            exclude_paths: List[str]
            dir_mtime:     Dict[str, float]
            return:        None

        Example
            >>> dump_cache('/path/pkg/__pycache__/__init__.dynamic-import.pyc', ...)
    '''
    with open(cache_path, 'w+b') as file:
        dump((version, recursive, exclude_paths, dir_mtime, data), file, MARSHAL_VERSION)


def load_cache(cache_path, recursive, exclude_paths):
    ''' Load cached file

        Type
            cache_path:    str
            recursive:     bool
            exclude_paths: List[str]
            return:        any

        Example
            >>> load_cache('/path/pkg/__pycache__/__init__.dynamic-import.pyc')
    '''
    with open(cache_path, 'rb') as file:
        try:
            cached_version, cached_recursive, cached_exclude_paths, dir_mtime, data = load(file)
        except Exception:
            # print()
            # print('importer() - error happened')
            # print()
            return None

        # check if `importer()` package version has changed!
        if version != cached_version:
            # print()
            # print('importer() - `version` has changed!')
            # print()
            return None
        elif recursive != cached_recursive:
            # print()
            # print('importer() - `recursive` has changed!')
            # print()
            return None
        elif exclude_paths != cached_exclude_paths:
            # print()
            # print('importer() - `exclude_paths` has changed!')
            # print()
            return None
        else:
            # check if dir has changed.
            for dir_path, mtime in dir_mtime.items():
                if mtime != mtime_it(dir_path):
                    # print()
                    # print('importer() - dir `mtime` has changed!')
                    # print()
                    return None

            # check if each of the the files have changed.
            # files = {}
            for _, file_path, _, mtime in data.values():
                # print('file_path:', file_path, mtime)
                if mtime != mtime_it(file_path):
                    # print()
                    # print('importer() - file `mtime` has changed!')
                    # print()
                    return None

        # TODO: check if files have been modified since the cache was created.
        # print('load version:', cached_version)
        # print('load recursive:', cached_recursive)
        # print('load exclude_paths:', cached_exclude_paths)
        # print('load dir_mtime:', dir_mtime)
        # print('load data:', data)

        return data
