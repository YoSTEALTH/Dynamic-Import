import sys
from types import ModuleType

__version__ = '0.9.4'
__all__ = ('importer', 'rearrange', 'Module')


def importer(_all_, *temp):
    ''' Dynamic run-time importer and easy to use module import path name.

        Type
            _all_: Dict[str, Iterable[str]]
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
              e.g. "from .module import example" before "importer()" is called.
            - You can also use "." e.g. '.one': ('a', 'b', 'c')
            - for 1 word import name you can use 'module': 'myclass' vs
              'module': ('myclass',)
            - All import names must be unique.

        Info
            - Inspired by "werkzeug" dynamic importer.
    '''
    try:
        # Automatically get "importer()" callers package name
        package = sys._getframe(1).f_locals['__package__']
        # Note
        #   This weird looking code is a hack job to avoid using "inspect"
        #   module as it was adding 300-800% slowdown on run-time.
    except KeyError:
        _ = ('"importer()" must be used/called inside "__init__.py" file')
        raise ImportError(_) from None

    # TODO
    if temp:
        # Temp fix. User haven't changed their "importer()" argument from
        # < "0.9.4". Lets account for it for now, will raise DeprecationWarning
        # in the future.
        if _all_ == package and isinstance(temp[0], dict):
            _all_ = temp[0]
        else:
            _ = 'Arguments you have provided does NOT seem right. \
            Use help(importer) to see how to use "importer()" function.'
            raise ValueError(_)

    # Organize import module & variable names ready to be used.
    _all, _reverse = rearrange(package, _all_)

    # Start new module import handler
    module = Module(package, _all, _reverse)

    # Note
    #   Since "importer()" is located in "__init__.py" file
    #   the package is already created, so lets use that.
    current_module = sys.modules[package]

    # Note
    #   - lets keep everything from the current module as is.
    #   - enables importing directly before "importer()" is called.
    #   - also doesn't break features like exceptions, ...
    module.__dict__.update(current_module.__dict__)

    # Lets switch new module with the current module.
    sys.modules[package] = module


def rearrange(pkg, all):
    ''' Rearrange "all" and produce value to key dict (_reverse)

        Type
            pkg: str
            all: str, Iterable[str]
            return: Tuple[Dict[str, str], Dict[str, str]]

        Example
            >>> _all, _reverse = _arrange(
            ...     'sample',
            ...     {
            ...         '.one': ('a', 'b', 'c'),
            ...         '.two': ('x', 'y', 'z'),
            ...         '.local': 'internals',
            ...         '.sub': {
            ...             '.page': ('e', 'f', 'g'),
            ...             '.name': 'name',
            ...         },
            ...     }
            ... )
            >>> _all
            {
                'sample.one': ('a', 'b', 'c')
                'sample.two': ('x', 'y', 'z')
                'sample.local': ('internals',)
                'sample.sub.page': ('e', 'f', 'g')
                'sample.sub.name': ('name',)
            }
            >>> _reverse
            {
                'a': sample.one
                'b': sample.one
                'c': sample.one
                'x': sample.two
                'y': sample.two
                'z': sample.two
                'internals': sample.local
                'e': sample.sub.page
                'f': sample.sub.page
                'g': sample.sub.page
                'name': sample.sub.name
            }
    '''
    a = {}  # {'test.one': ('a', 'b', 'c'), ...}
    r = {}  # {'a': 'test.one', ...}
    for key, value in all.items():
        # Lets convert relative to static import!
        # e.g: '.one' -to-> 'test.one'
        key = f'{pkg}{key}' if key[0] == '.' else f'{pkg}.{key}'

        # Lets wrap tuple around str value.
        if isinstance(value, str):
            value = (value,)
        elif isinstance(value, dict):
            # Sub-Package - Recursive
            sub_all, sub_reverse = rearrange(key, value)
            a.update(sub_all)
            r.update(sub_reverse)
            continue

        # New __all__ Holder
        a[key] = value

        # Lest reverse assign value to key
        # e.g: {'test.one': ('a', 'b', 'c')} -to-> {'a: 'test.one', ...}
        for attr in value:
            r[attr] = key

    return a, r


class Module(ModuleType):
    # ModuleType = type(sys.modules)

    def __init__(self, pkg, _all, _reverse, *args, **kwargs):
        # Assign
        self.___all = _all  # {'test.one': ('a', 'b', 'c'), ...}
        self.___reverse = _reverse  # {'a': 'test.one', ...}

        # Run original ModuleType.__init__
        super().__init__(pkg, None, *args, **kwargs)

    def __getattr__(self, name):
        # e.g: 'a' in {'a': 'test.one', ...}
        if name in self.___reverse:
            # Lets import the file the "name" variable is in.
            module = __import__(
                # e.g: self.___reverse[name]="test.one" and name="a"
                self.___reverse[name], None, None, [name]
                # Note
                #   If there is an error inside "__import__()" it will raise
                #   ImportError even if its not related to import as
                #   sub-error message is suppressed by "__import__()" it seems.
            )

            # Note
            #   Lets also assign rest of the instance(s) belonging to
            #   the same module while we are at it, so we don't have to
            #   re-import them again!

            # e.g: 'a' in ['a', 'b', 'c']
            for attr in self.___all[module.__name__]:
                self.__dict__[attr] = module.__dict__[attr]
                # setattr(self, attr, getattr(module, attr))

            # Lets return dynamically imported module
            return self.__dict__[name]
            # return getattr(module, name)

        # Stragglers, lets let ModuleType handle it.
        return ModuleType.__getattribute__(self, name)

    def __dir__(self):
        # Lets ignore internally used instances we created.
        ignore = {'___all', '___reverse'}
        # Nice and clean "dir(test)" printout.
        return [attr for attr in self.__dict__ if attr not in ignore]
