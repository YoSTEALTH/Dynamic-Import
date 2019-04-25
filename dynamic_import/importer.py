import sys
from .rearrange import rearrange
from .module import Module

__all__ = ('importer',)


def importer(all, *temp):
    ''' Dynamic run-time importer and easy to use module import path name.

        Type
            all:    Dict[str, Union[str, Iterable[str], Dict[...]]]
            temp:   Tuple[any]  # note: This argument will be removed starting v1.0
            return: None

        Example
            >>> importer(
            ...     {
            ...     'one': ('a', 'b', 'c'),  # from .one import a, b, c
            ...     'two': ('x', 'y', 'z'),  # from .two import x, y, z
            ...     'local': 'internals',    # from .local import internals
            ...     'sub': {
            ...         'page': ('e', 'f', 'g'),  # from .sub.page import e,...
            ...         'name': 'name',           # from .sub.name import name
            ...         }
            ...     }
            ... )

        Note
            - you can still use static/normal import
              e.g. ```from .module import example``` before `importer()` is called.
            - You can also use `.` e.g. ```'.one': ('a', 'b', 'c')```
            - for 1 word import name you can use ```'module': 'myclass'``` vs
              ```'module': ('myclass',)```
            - All import names must be unique.

        Info
            - Inspired by "werkzeug" dynamic importer.
    '''
    try:
        # Automatically get `importer()` callers package name
        package = sys._getframe(1).f_globals['__package__']
        # Note
        #   This weird looking code is a hack job to avoid using `inspect`
        #   module as it was adding 300-800% slowdown on run-time.
    except KeyError:
        _ = '`importer()` must be called from within `__init__.py`'
        raise ImportError(_) from None
    else:
        if not package:
            _ = '`importer()` must be called from within `__init__.py`'
            raise ImportError(_)

    if temp:
        _ = 'No need to manually provide `__package__` into `importer()`'
        raise DeprecationWarning(_)
        # TODO
        #     - Starting from 1.0 `temp` argument will be removed.

    # Organize import module & variable names ready to be used.
    _all, reverse = rearrange(package, all)

    # Start new module import handler
    module = Module(package, _all, reverse)

    # Note
    #   Since `importer()` is located in `__init__.py` file
    #   the package is already created, so lets use that.
    current_module = sys.modules[package]

    # Note
    #   - lets keep everything from the current module as is.
    #   - enables importing directly before `importer()` is called.
    #   - also doesn't break features like exceptions, ...
    module.__dict__.update(current_module.__dict__)

    # Lets switch new module with the current module.
    sys.modules[package] = module
