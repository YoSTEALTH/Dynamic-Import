from types import ModuleType
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader, ExtensionFileLoader
from .prep import EXT_SUFFIX


__all__ = 'Module',


class Module(ModuleType):

    __slots__ = '__PACKAGE__', '__INFO__'

    def __init__(self, package, info, module, *args, **kwargs):
        ''' Dynamic import module

            Type
                package: str
                info:    Dict[str, Tuple[str, str, Union[List[str], Tuple[str]]]]
                module:  sys
                args:    Tuple[any]
                kwargs:  Dict[str, any]
                return:  None
        '''
        self.__PACKAGE__ = package
        self.__INFO__ = info
        # note: ^ this needs to mimic magic method name since those are made to raise error
        self.__dict__.update(module.__dict__)
        setattr(self, '__all__', (*self.__dict__, *self.__INFO__))

        # TODO: what does this actually do?
        # super().__init__(package, None, *args, **kwargs)

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
        '''
        # print('__getattr__', name)
        if name in self.__INFO__:
            # print('__INFO__', name)
            module_name, module_path, variables, _ = self.__INFO__[name]
            if module_path.endswith(EXT_SUFFIX[0]):  # e.g: '.py'
                loader = SourceFileLoader(module_name, module_path)
            elif module_path.endswith(EXT_SUFFIX[1:]):  # e.g: '.cpython-312-x86_64-linux-gnu.so'
                loader = ExtensionFileLoader(module_name, module_path)
            else:
                raise NotImplementedError(f'`Module()` {module_path!r} extension type.')
            spec = spec_from_loader(loader.name, loader)
            module = module_from_spec(spec)
            # print('dir:', dir(module))
            loader.exec_module(module)

            # add all the variables found in modules `__all__` into `self`
            for var in variables:
                setattr(self, var, getattr(module, var))
            return getattr(self, name)
        # elif name == '__all__':
        #     # support `from module import *` & `module.__all__` lookup
        #     print('__all__')
        #     # if self.__ALL__ is None:
        #     #     # self.__ALL__ = tuple(self.__INFO__.keys())
        #     #     self.__ALL__ = (*self.__dict__, *self.__INFO__)
        #     return self.__all__
        else:
            try:
                return super().__getattr__(name)
            except AttributeError:
                error = f'module {self.__PACKAGE__!r} has no attribute {name!r}\n'
                raise AttributeError(error) from None


# working really good:
# from types import ModuleType
# from importlib.util import spec_from_loader, module_from_spec
# from importlib.machinery import SourceFileLoader, ExtensionFileLoader
# from .prep import EXT_SUFFIX


# __all__ = 'Module',


# class Module(ModuleType):

#     def __init__(self, package, info, module, *args, **kwargs):
#         ''' Dynamic import module

#             Type
#                 package: str
#                 info:    Dict[str, Tuple[str, str, Union[List[str], Tuple[str]]]]
#                 module:  sys
#                 args:    Tuple[any]
#                 kwargs:  Dict[str, any]
#                 return:  None
#         '''
#         self.__PACKAGE__ = package
#         self.__INFO__ = info
#         self.__ALL__ = None
#         # note: ^ this needs to mimic magic method name since those are made to raise error
#         self.__dict__.update(module.__dict__)
#         super().__init__(package, None, *args, **kwargs)

#     def __getattr__(self, name):
#         '''
#             Type
#                 name:   str
#                 return: any

#             Example
#                 >>> from pkg import one

#                 # or

#                 >>> import pkg
#                 >>> pkg.one()
#         '''
#         if name in self.__INFO__:
#             module_name, module_path, variables = self.__INFO__[name]
#             if module_path.endswith(EXT_SUFFIX[0]):  # e.g: '.py'
#                 loader = SourceFileLoader(module_name, module_path)
#             elif module_path.endswith(EXT_SUFFIX[1:]):  # e.g: '.cpython-312-x86_64-linux-gnu.so'
#                 loader = ExtensionFileLoader(module_name, module_path)
#             else:
#                 raise NotImplementedError(f'`Module()` {module_path!r} extension type.')
#             spec = spec_from_loader(loader.name, loader)
#             module = module_from_spec(spec)
#             loader.exec_module(module)

#             # add all the variables found in modules `__all__` into `self`
#             for var in variables:
#                 setattr(self, var, getattr(module, var))
#             return getattr(self, name)
#         elif name == '__all__':
#             # support `from module import *` & `module.__all__` lookup
#             if self.__ALL__ is None:
#                 self.__ALL__ = tuple(self.__INFO__.keys())
#             return self.__ALL__
#         else:
#             try:
#                 return super().__getattr__(name)
#             except AttributeError:
#                 _ = f'module {self.__PACKAGE__!r} has no attribute {name!r}'
#                 raise AttributeError(_) from None

