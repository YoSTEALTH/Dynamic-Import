import sys
from types import ModuleType

__all__ = ('importer',)


def importer(__package__, __all__):
    ''' Dynamic run-time importer and easy to use module import path name.

        Type
            __package__: str
            __all__: Dict[str, Iterable[str]]
            return: None

        Example
            >>> importer(
            ...     __package__,  # can also use "sample"
            ...     {
            ...         '.one': ('a', 'b', 'c'),  # from .one import 'a', ...
            ...         '.two': ('x', 'y', 'z')
            ...     }
            ... )

        Note
            - Inspired by "werkzeug" dynamic importer.
    '''
    # Originize import module & variable names ready to be used.
    _all, _reverse = _arrange(__package__, __all__)

    # Start new module import handler
    module = _Module(__package__, _all, _reverse)

    # Note
    #   Since "importer()" is located in "__init__.py" file
    #   the package is already created, so lets use that.
    current_module = sys.modules[__package__]

    # Note
    #   - lets keep everything from the current module as is.
    #   - enables importing directly before "importer()" is called.
    #   - also doesn't break features like exceptions, ...
    module.__dict__.update(current_module.__dict__)

    # Lets switch new module with the current module.
    sys.modules[__package__] = module


# Internally used function & class
# v------------------------------v

def _arrange(pkg, all):
    ''' Arrange "all" and produce value to key dict (_reverse)

        Type
            pkg: str
            all: str, Iterable[str]
            return: Tuple[Dict[str, str], Dict[str, str]]

        Example
            >>> _all, _reverse = _arrange(
            ...     'sample',
            ...     {
            ...         '.one': ('a', 'b', 'c'),  # from .one import a, b, c
            ...         '.two': ('x', 'y', 'z'),  # from .two import x, y, z
            ...         '.local': 'o_o',          # from .local import o_o
            ...     }
            ... )
            >>> _all
            {
                'sample.one': ('a', 'b', 'c'),
                'sample.two': ('x', 'y', 'z'),
                'sample.local': ('o_o',)
            }
            >>> _reverse
            {
                'a': 'sample.one',
                'b': 'sample.one',
                'c': 'sample.one',
                'x': 'sample.two',
                'y': 'sample.two',
                'z': 'sample.two',
                'o_o':'sample.local'
            }
    '''
    a = {}  # {'test.one': ('a', 'b', 'c'), ...}
    r = {}  # {'a': 'test.one', ...}
    for key, value in all.items():
        # Lets wrap tuple around str value.
        if isinstance(value, str):
            value = (value,)

        # Lets convert relative to static import!
        # e.g: '.one' -to-> 'test.one'
        if key[0] == '.':
            key = pkg + key

        # New __all__ Holder
        a[key] = value

        # Lest reverse assign value to key
        # e.g: {'test.one': ('a', 'b', 'c')} -to-> {'a: 'test.one', ...}
        for attr in value:
            r[attr] = key

    return a, r


class _Module(ModuleType):
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
                # note:
                #   If there is an error inside "__imort__()" it will raise
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
