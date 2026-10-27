from importlib import import_module
from importlib._bootstrap import _ModuleLockManager as module_lock  # same per-module lock `import` uses
from importlib.machinery import ExtensionFileLoader, SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from sys import modules
from types import ModuleType
from .prep import EXT_SUFFIX
from .special import special


__all__ = 'Module',


class Module(ModuleType):

    __slots__ = '__PACKAGE__', '__INFO__', '__ORIGINAL__'

    def __init__(self, package, info, module, *args, **kwargs):
        ''' Dynamic import module

            Type
                package: str
                info:    dict[str, tuple[str, str, list[str] | tuple[str]]]
                module:  ModuleType
                args:    tuple[any]
                kwargs:  dict[str, any]
                return:  None

            Note
                - `module` is the package module that called `importer()`. Its `__init__.py` is still
                  running at that point, so names defined after the `importer()` call are read from it
                  lazily by `__getattr__` instead of executing `__init__.py` a second time.
        '''
        super().__init__(package, None, *args, **kwargs)
        self.__PACKAGE__ = package
        self.__INFO__ = info
        self.__ORIGINAL__ = module
        # note: ^ these needs to mimic magic method name since those are made to raise error

        # only include special name from previous module, all other names should be
        # imported through this `Module`
        for key, value in module.__dict__.items():
            if (key[0:2] == '__' == key[-2:]) and (key[2] != '_' != key[-3]):
                self.__dict__[key] = value  # only update `__special__` names
        setattr(self, '__all__', (*self.__dict__, *self.__INFO__))

    def __dir__(self):
        '''
            Example:
                >>> import library
                >>> dir(library)
                [....]

            Note:
                - returns all names without actually loading the module yet!
        '''
        return self.__all__

    def __getattr__(self, name):
        '''
            Type
                name:   str
                return: any

            Example
                >>> from pkg import one

                # or

                >>> import pkg
                >>> pkg.one()

            Note
                - the sub-module is registered in `sys.modules` before it runs, so a later
                  `import pkg.sub.module` reuses it instead of executing the file again.
                - loading is guarded by the import system's per-module lock, so two threads
                  asking for the same name execute the sub-module only once.
        '''
        if name in self.__INFO__:
            module_name, module_path, variables, _ = self.__INFO__[name]
            if module_path.endswith(EXT_SUFFIX[0]):  # e.g: '.py'
                loader = SourceFileLoader(module_name, module_path)
            elif module_path.endswith(EXT_SUFFIX[1:]):  # e.g: '.cpython-312-x86_64-linux-gnu.so'
                loader = ExtensionFileLoader(module_name, module_path)
            else:
                raise NotImplementedError(f'`Module()` {module_path!r} extension type.')

            with module_lock(module_name):
                if name in self.__dict__:
                    return self.__dict__[name]  # another thread loaded it while we waited.

                if module_name == self.__PACKAGE__:
                    module = self.__ORIGINAL__  # defined in the package's own `__init__.py`
                elif (module := modules.get(module_name)) is None:
                    # like `import pkg.sub.mod`: parent packages must exist for later absolute imports.
                    parent_name, _, child_name = module_name.rpartition('.')
                    if (parent := modules.get(parent_name)) is None:
                        parent = import_module(parent_name)
                    spec = spec_from_loader(loader.name, loader)
                    module = module_from_spec(spec)
                    modules[module_name] = module
                    spec._initializing = True  # makes a concurrent `import` of this module wait for us
                    try:
                        loader.exec_module(module)
                    except BaseException:
                        modules.pop(module_name, None)
                        raise
                    finally:
                        spec._initializing = False
                    if not isinstance(parent, Module):
                        setattr(parent, child_name, module)  # `Module` parents expose names via `__INFO__`

                # add all the variables found in modules `__all__` into `self` (special names are ignored)
                for var in special(variables):
                    try:
                        value = getattr(module, var)
                    except AttributeError:
                        error = f'cannot import name {var!r} from {module_name!r} ({module_path}): ' \
                                'it is listed in `__all__` but the module does not define it.'
                        raise ImportError(error, name=module_name, path=module_path) from None
                    setattr(self, var, value)
            return getattr(self, name)
        else:
            try:
                return super().__getattr__(name)
            except AttributeError:
                error = f'module {self.__PACKAGE__!r} has no attribute {name!r}\n'
                raise AttributeError(error) from None
