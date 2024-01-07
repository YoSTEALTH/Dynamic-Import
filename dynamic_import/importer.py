from os import remove
from sys import _getframe, modules
from os.path import exists
try:
    from functools import cache
except ImportError:  # account for python 3.8
    from functools import lru_cache as cache
from .module import Module
from .check import importer_called, exclude_directory
from .cache import pkg_cache_path, create_cache_dir, dump_cache, load_cache
from .prep import prep_package


__all__ = 'importer',
ERROR_MSG = '`importer()` must be called from within `__init__.py`'


@cache
def importer(*, cache=True, recursive=True, exclude=None, exclude_dir=None):
    ''' Automatically import modules dynamically.

        Type
            cache:       bool
            recursive:   bool
            exclude:     Union[Tuple[str], str, None]
            exclude_dir: Union[Tuple[str], str, None]
            return:      None

        Example
            # /pkg/__init__.py
            >>> from importer import importer
            ...
            >>> importer()

            # to disable cache (for temporary use only!)
            >>> importer(cache=False)

            # prevent scanning sub-directories
            >>> importer(recursive=False)
            
            # TODO: exclude `.py, .so` file
            >>> importer(exclude_dir=('/path/pkg/ignore_this_file.py', ...))

            # exclude sub-directory
            >>> importer(exclude_dir=('/path/pkg/sub-dir', ...))

        Note:
            - `importer()` on first run will scan all the `.py` files for `__all__` or variables to later import them
               dynamically.
            - for production `importer(cache)` must be set to default `True` as cache is what makes the `importer()`
              fast and dynamic.
    '''
    caller = _getframe(1).f_globals  # get info of where `importer()` is being called from
    # note: avoiding using `inspect` module as it was adding 300-800% slowdown on run-time
    try:
        package = caller['__package__']
        pkg_path = caller['__file__']
    except KeyError:
        raise ImportError(ERROR_MSG) from None

    if exclude:
        raise NotImplementedError('importer(exclude)')

    if not package or not pkg_path.endswith('/__init__.py'):
        raise ImportError(ERROR_MSG)

    # check if `importer()` was previously called.
    importer_called(pkg_path)

    # exclude sub directories
    if recursive and exclude_dir:
        exclude_paths = exclude_directory(exclude_dir, pkg_path)
    else:
        exclude_paths = []

    cache_path = pkg_cache_path(pkg_path, 'importer')

    if cache:
        while True:
            if exists(cache_path):
                if info := load_cache(cache_path, recursive, exclude_paths):
                    break
                else:
                    remove(cache_path)
                    continue
            else:
                try:
                    info, dir_mtime = prep_package(pkg_path, recursive)
                    create_cache_dir(cache_path)
                    dump_cache(cache_path, info, recursive, exclude_paths, dir_mtime)
                    break
                except Exception as e:
                    if exists(cache_path):
                        remove(cache_path)
                    raise e from None
    else:
        if exists(cache_path):
            remove(cache_path)
        info, _ = prep_package(pkg_path, recursive)

    if (module := modules.pop(package, None)) is None:
        error = f'`importer()` can not find package {package!r}'
        raise ImportError(error)

    modules[package] = Module(package, info, module)
