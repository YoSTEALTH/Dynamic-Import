import sys
from types import ModuleType

__all__ = ('importer',)
__version__ = '0.9.1'


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
    # Start new module import handler
    module = Module(__package__, __all__)

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


class Module(ModuleType):
    # ModuleType = type(sys.modules)

    def __init__(self, pkg, _all, *args, **kwargs):
        reverse = {}
        for key, values in _all.items():
            # Lets convert relative to static import!
            # e.g: '.one' -to-> 'test.one'
            if key[0:1] == '.':
                old_key = key
                key = pkg + old_key
                _all[key] = _all.pop(old_key)

            # Lest reverse assign values to key
            # e.g: {'test.one': ('a', 'b', 'c')} -to-> {'a: 'test.one', ...}
            for attr in values:
                reverse[attr] = key

        # Assign
        self.___all = _all  # {'test.one': ('a', 'b', 'c'), ...}
        self.___reverse = reverse  # {'a': 'test.one', ...}

        # Run original ModuleType.__init__
        super().__init__(pkg, None, *args, **kwargs)

    def __getattr__(self, name):
        # e.g: 'a' in {'a': 'test.one', ...}
        if name in self.___reverse:
            # Lets import the file the "name" variable is in.
            module = __import__(
                # e.g: self.___reverse[name]="test.one" and name="a"
                self.___reverse[name], None, None, [name]
            )

            # Note
            #   Lets also assign rest of the instance(s) belonging to
            #   the same module while we are at it, so we don't have to
            #   re-import them again!

            # e.g: 'a' in ['a', 'b', 'c']
            for attr in self.___all[module.__name__]:
                # > setattr(self, attr, getattr(module, attr))
                self.__dict__[attr] = module.__dict__[attr]

            # Lets return dynamically imported module
            return self.__dict__[name]  # > getattr(module, name)

        # Stragglers, lets let ModuleType handle it.
        return ModuleType.__getattribute__(self, name)

    def __dir__(self):
        # Lets ignore internally used instances we created.
        ignore = {'___all', '___reverse'}
        # Nice and clean "dir(test)" printout.
        return [attr for attr in self.__dict__ if attr not in ignore]
