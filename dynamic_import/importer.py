from os import altsep, remove, sep
from os.path import join, split
from sys import _getframe, modules
from .cache import create_cache_dir, dump_cache, load_cache, pkg_cache_path
from .check import exclude_dir_check, exclude_file_check, importer_called
from .module import Module
from .prep import prep_package
from .record import add_record
from .version import version


__all__ = 'importer',


def importer(*, cache=True, recursive=True, exclude_file=None, exclude_dir=None):
    ''' Automatically import modules dynamically.

        Type
            cache:        bool
            recursive:    bool
            exclude_file: tuple[str] | str | None
            exclude_dir:  tuple[str] | str | None
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
            - if the cache file can not be read, written or removed (e.g. package installed into a read-only
              `site-packages`) `importer()` silently runs without cache.
    '''
    caller = _getframe(1).f_globals  # get info of where `importer()` is being called from
    # note: avoiding using `inspect` module as it was adding 300-800% slowdown on run-time
    pkg_name = caller['__package__']
    file_path = caller['__file__']
    pkg_dir, init_file = split(file_path)  # '/path/pkg', '__init__.py'
    if altsep:  # Windows: a `sys.path` entry may use '/', `walk()` and `normpath()` give '\'
        pkg_dir = pkg_dir.replace(altsep, sep)
    pkg_path = join(pkg_dir, '')  # '/path/pkg' to '/path/pkg/'

    if not pkg_name or init_file != '__init__.py':
        raise ImportError('`importer()` must be called from within `__init__.py`')

    exclude_file_path = exclude_file_check(exclude_file, pkg_path)  # type: list
    exclude_dir_path = exclude_dir_check(exclude_dir, pkg_path, recursive)  # type: list

    # check if `importer()` was previously called.
    if importer_called(pkg_path, recursive, exclude_dir_path):
        return None
        # Python tends to call `__init__.py` again if there are other defines
        # var, func, ... with `importer()` already being called. So its better
        # to ignore since module is already created.

    cache_path = pkg_cache_path(pkg_path, init_file, 'importer')  # type: str
    info = None
    if cache:
        # `None` if missing, unreadable or stale: rescan, `dump_cache()` replaces the old file.
        info = load_cache(cache_path, recursive, exclude_file_path, exclude_dir_path, version)
    else:
        try:
            remove(cache_path)
        except OSError:
            pass  # no cache file, or can not remove it.

    if info is None:
        info, dir_mtime = prep_package(pkg_name, pkg_path, recursive, exclude_file_path, exclude_dir_path)
        if cache:
            try:
                create_cache_dir(cache_path)
                dump_cache(cache_path, info, recursive, exclude_file_path, exclude_dir_path, dir_mtime, version)
                if cache_path.startswith(pkg_path):  # not relocated by `sys.pycache_prefix`
                    add_record(pkg_name, cache_path)
            except OSError:
                pass  # read-only install (e.g. root owned `site-packages`), run without cache.

    module = modules.get(pkg_name)
    modules[pkg_name] = Module(pkg_name, info, module)
