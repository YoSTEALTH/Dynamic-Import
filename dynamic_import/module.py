from types import ModuleType

__all__ = ('Module',)


class Module(ModuleType):  # ModuleType = type(sys.modules)

    def __init__(self, pkg, all, reverse, *args, **kwargs):
        '''
            Type
                pkg:        str
                all:        Dict[str, Tuple[str]],
                reverse:    Dict[str, str]
                args:       Tuple[any]
                kwargs:     Dict[str, any]
                return: None
        '''
        # Mask as special attribute to avoid user overwriting attribute name with module name
        self.__importer_all__ = all  # {'test.one': ('a', 'b', 'c'), ...}
        self.__importer_reverse__ = reverse  # {'a': 'test.one', ...}

        # Run original ModuleType.__init__
        super().__init__(pkg, None, *args, **kwargs)

    def __getattr__(self, name):
        '''
            Type
                name:   str
                return: object
        '''
        # e.g: 'a' in {'a': 'test.one', ...}
        if name in self.__importer_reverse__:
            try:
                # Lets import the file the "name" variable is in.
                module = __import__(
                    # e.g: self.___reverse[name]="test.one" and name="a"
                    self.__importer_reverse__[name], None, None, [name]
                    # Note
                    #   If there is an error inside "__import__()" it will
                    #   raise ImportError even if its not related to import as
                    #   sub-error message is suppressed by "__import__()"
                    #   it seems.
                )
            except ModuleNotFoundError:
                # This error is a bit more clear vs normal error message.
                _ = (f'No module named {self.__importer_reverse__[name]!r} located '
                     f'while trying to import {name!r}')
                raise ImportError(_) from None
            else:
                # Note
                #   Lets also assign rest of the instance(s) belonging to
                #   the same module while we are at it, so we don't have to
                #   re-import them again!

                # e.g: 'a' in ['a', 'b', 'c']
                for attr in self.__importer_all__[module.__name__]:
                    self.__dict__[attr] = module.__dict__[attr]

                # Lets return dynamically imported module
                return self.__dict__[name]

        # Stragglers, lets let ModuleType handle it.
        return ModuleType.__getattribute__(self, name)

    def __dir__(self):
        # Lets ignore internally used instances we created.
        ignore = {'__importer_all__', '__importer_reverse__'}
        # Nice and clean "dir(test)" printout.
        return [attr for attr in self.__dict__ if attr not in ignore]
