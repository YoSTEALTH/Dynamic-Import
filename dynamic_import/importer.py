from os import remove
from sys import _getframe, modules
from os.path import exists, split
try:
    from functools import cache
except ImportError:  # account for python 3.8
    from functools import lru_cache as cache
from .module import Module
from .check import importer_called, exclude_file_check, exclude_dir_check
from .cache import pkg_cache_path, create_cache_dir, dump_cache, load_cache
from .prep import prep_package


__all__ = 'importer',
ERROR_MSG = '`importer()` must be called from within `__init__.py`'


@cache
def importer(*, cache=True, recursive=True, exclude_file=None, exclude_dir=None):
    ''' Automatically import modules dynamically.

        Type
            cache:        bool
            recursive:    bool
            exclude_file: Union[Tuple[str], str, None]
            exclude_dir:  Union[Tuple[str], str, None]
            return:       None

        Example
            # /pkg/__init__.py
            >>> from importer import importer
            ...
            >>> importer()

            # to disable cache (for temporary use only!)
            >>> importer(cache=False)

            # prevent scanning sub-directories
            >>> importer(recursive=False)
            
            # exclude `.py, .so` file
            >>> importer(exclude_file='file.py')                            # single
            >>> importer(exclude_file=('file.py', 'sub-dir/file.py', ...))  # multiple

            # exclude sub-directory
            >>> importer(exclude_dir='sub-dir')                        # single
            >>> importer(exclude_dir=('sub-dir', 'sub/sub-dir', ...))  # multiple

        Note:
            - `importer()` on first run will scan all the `.py` files for `__all__` or variables to later import them
               dynamically.
            - for production `importer(cache)` must be set to default `True` as cache is what makes the `importer()`
              fast and dynamic.
    '''
    caller = _getframe(1).f_globals  # get info of where `importer()` is being called from
    # note: avoiding using `inspect` module as it was adding 300-800% slowdown on run-time
    try:
        pkg_name = caller['__package__']
        file_path = caller['__file__']
    except KeyError:
        raise ImportError(ERROR_MSG) from None
    else:
        pkg_dir, init_file = split(file_path)  # '/path/pkg', '__init__.py'
        pkg_path = f'{pkg_dir}/'  # '/path/pkg' to '/path/pkg/'

    if not pkg_name or init_file != '__init__.py':
        raise ImportError(ERROR_MSG)

    # check if `importer()` was previously called.
    importer_called(pkg_path)
    # exclude file
    exclude_file_path = exclude_file_check(exclude_file, pkg_name, pkg_path)  # type: list
    # exclude sub directories
    exclude_dir_path = exclude_dir_check(exclude_dir, pkg_path, recursive)  # type: list
    cache_path = pkg_cache_path(pkg_path, init_file, 'importer')  # type: str
    if cache:
        while True:
            if exists(cache_path):
                if info := load_cache(cache_path, recursive, exclude_file_path, exclude_dir_path):
                    break
                else:
                    remove(cache_path)
                    continue
            else:
                try:
                    info, dir_mtime = prep_package(pkg_name, pkg_path, recursive, exclude_file_path, exclude_dir_path)
                    create_cache_dir(cache_path)
                    dump_cache(cache_path, info, recursive, exclude_file_path, exclude_dir_path, dir_mtime)
                    break
                except Exception as e:
                    if exists(cache_path):
                        remove(cache_path)
                    raise e from None
    else:
        if exists(cache_path):
            remove(cache_path)
        info, _ = prep_package(pkg_name, pkg_path, recursive, exclude_file_path, exclude_dir_path)

    if (module := modules.pop(pkg_name, None)) is None:
        error = f'`importer()` can not find package {pkg_name!r}'
        raise ImportError(error)

    modules[pkg_name] = Module(pkg_name, info, module)
