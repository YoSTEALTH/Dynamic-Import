import re
import pytest
from types import ModuleType
from dynamic_import.prep import EXT_SUFFIX, prep_package
from dynamic_import.module import Module


def test_module():
    recursive = True
    pkg_name = 'basic'
    pkg_path = 'test/basic/'
    exclude_file = ['test/basic/sub/skip-me.py']
    exclude_dir = ['test/basic/skip/']
    info, dir_mtime = prep_package(pkg_name, pkg_path, recursive, exclude_file, exclude_dir)
    find = ['DEFINE', 'MyClass', 'child', 'five', 'four', 'my_async_func', 'my_function', 'one',
            're_import', 'three', 'two', 'var']

    # inject just to test
    info['bad_ext'] = ('basic.bad_ext', 'test/basic/bad_ext.bad', ('bad_ext',), 123.45)
    info['so_file'] = ('basic.so_file', 'test/basic/so_file.so', ('so_file',), 123.45)
    find.append('bad_ext')
    find.append('so_file')

    for i, ext in enumerate(EXT_SUFFIX):
        name = f'file_{i}'
        info[name] = (f'basic.{name}', f'test/basic/{name}{ext}', (name,), 123.45)
        find.append(name)

    module = Module(pkg_name, info, ModuleType)
    assert [i for i in sorted(dir(module)) if i[0] != "_"] == sorted(find)

    with pytest.raises(NotImplementedError, match=re.escape("`Module()` 'test/basic/bad_ext.bad' extension type.")):
        module.bad_ext

    with pytest.raises(NotImplementedError, match=re.escape("`Module()` 'test/basic/so_file.so' extension type.")):
        module.so_file

    # check
    for i, ext in enumerate(EXT_SUFFIX):
        if ext == '.py':
            with pytest.raises(FileNotFoundError):
                getattr(module, f'file_{i}')
        else:
            with pytest.raises(ImportError):
                getattr(module, f'file_{i}')


def test_calling_from_not_init():
    with pytest.raises(ImportError, match=re.escape("`importer()` must be called from within `__init__.py`")):
        import error_test.not_init  # noqa
