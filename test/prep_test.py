import sys
from importlib.machinery import EXTENSION_SUFFIXES
from os.path import join
import pytest
from conftest import native
from dynamic_import.prep import EXT_SUFFIX, is_extension, prep_package, prep_variables


def test_cache():
    # every suffix the interpreter can import, e.g: ('.py', '.cpython-315-x86_64-linux-gnu.so', ..., '.so')
    assert EXT_SUFFIX == ('.py', *EXTENSION_SUFFIXES)
    cpython = EXT_SUFFIX[1]
    if sys.platform == 'win32':  # ('.py', '.cp315-win_amd64.pyd', '.pyd')
        assert cpython.startswith('.cp3') and cpython.endswith('.pyd')
        assert EXT_SUFFIX[-1] == '.pyd'
    else:  # Linux, macOS: ('.py', '.cpython-315-x86_64-linux-gnu.so', '.abi3.so', ..., '.so')
        assert cpython.startswith('.cpython-') and cpython.endswith('.so')
        assert EXT_SUFFIX[-1] == '.so'


def test_is_extension(tmp_dir):
    def ext(data, name='foo'):
        path = tmp_dir / f'{name}.so'
        path.write_bytes(data)
        return is_extension(str(path), name)

    assert ext(b'\x7fELF...PyInit_foo\0...')
    assert ext(b'..._PyInit_foo\0...')  # macOS symbol names start with `_`
    assert ext(b'...PyModExport_foo\0...')  # 3.15+ export hook
    assert ext(b'...PyInitU_' + 'é'.encode('punycode').replace(b'-', b'_') + b'\0...', 'é')  # non-ASCII name
    assert not ext(b'')
    assert not ext(b'...PyInit_foobar\0...')  # other module's init function
    assert not ext(b'...PyInit_foo...')  # not a whole symbol name
    assert not ext(b'\x7fELF...add\0...')  # plain shared library


def test_prep_data_dir(tmp_dir):
    # a directory without any module is still tracked, so a module added later invalidates the cache.
    pkg_path = tmp_dir / 'pkg'
    pkg_path.mkdir()
    (pkg_path / '__init__.py').write_text('')
    (pkg_path / 'data').mkdir()
    (pkg_path / 'data' / 'file.txt').write_text('')
    (pkg_path / 'data' / 'libfoo.so').write_text('')  # shared library, not a module (no `PyInit_libfoo`)
    (pkg_path / '__pycache__').mkdir()
    (pkg_path / '__pycache__' / 'x.py').write_text('')
    (pkg_path / 'skip').mkdir()
    (pkg_path / 'skip' / 'deep').mkdir()
    (pkg_path / 'skip' / 'deep' / 'mod.py').write_text('x = 1')
    # dotted names are never packages, e.g. macOS debug bundle `mod.so.dSYM/Contents/Resources/DWARF/mod.so`
    for dotted in ('mod.so.dSYM', '.hidden'):
        (pkg_path / dotted / 'deep').mkdir(parents=True)
        (pkg_path / dotted / 'deep' / 'mod.py').write_text('x = 1')

    info, dir_mtime = prep_package('pkg', join(pkg_path, ''), True, [], [join(pkg_path, 'skip', '')])
    assert info == {}
    # `__pycache__`, `skip/` and dotted directories not descended
    assert set(dir_mtime) == {join(pkg_path, ''), join(pkg_path, 'data', '')}

    (pkg_path / 'data' / 'mod.py').write_text('x = 1')
    info, _ = prep_package('pkg', join(pkg_path, ''), True, [], [])
    assert set(info) == {'x'}


def test_prep():
    # recusvie True test
    # ------------------
    match = {
             'DEFINE': ('basic',
                        'test/basic/__init__.py',
                        ('DEFINE', 're_import')),
             'MyClass': ('basic.sub.auto_find',
                         'test/basic/sub/auto_find.py',
                         ['my_function', 'var', 'MyClass', 'my_async_func']),
             'child': ('basic.sub.child.child',
                       'test/basic/sub/child/child.py',
                       ('child',)),
             'five': ('basic.sub.four_five',
                      'test/basic/sub/four_five.py',
                      ('four', 'five')),
             'four': ('basic.sub.four_five',
                      'test/basic/sub/four_five.py',
                      ('four', 'five')),
             'my_async_func': ('basic.sub.auto_find',
                               'test/basic/sub/auto_find.py',
                               ['my_function', 'var', 'MyClass', 'my_async_func']),
             'my_function': ('basic.sub.auto_find',
                             'test/basic/sub/auto_find.py',
                             ['my_function', 'var', 'MyClass', 'my_async_func']),
             'one': ('basic.one', 'test/basic/one.py', ('one',)),
             're_import': ('basic', 'test/basic/__init__.py',
                           ('DEFINE', 're_import')),
             'three': ('basic.sub.three', 'test/basic/sub/three.py', ['three']),
             'two': ('basic.two', 'test/basic/two.py', ('two',)),
             'var': ('basic.sub.auto_find',
                     'test/basic/sub/auto_find.py',
                     ['my_function', 'var', 'MyClass', 'my_async_func'])
             }
    match = {k: (module, native(path), variables) for k, (module, path, variables) in match.items()}
    find_dir_mtime = set(map(native, ('test/basic/',
                                      'test/basic/so/',
                                      'test/basic/sub/',
                                      'test/basic/sub/conflict/',
                                      'test/basic/sub/child/')))
    cached_match = {}
    recursive = True
    pkg_path = native('test/basic/')

    exclude_file = [native('test/basic/sub/skip-me.py')]
    exclude_dir = [native('test/basic/skip/')]

    info, dir_mtime = prep_package('basic', pkg_path, recursive, exclude_file, exclude_dir)
    for k, v in info.items():
        cached_match[k] = v[0:3]  # note: ignore the last file modification time.

    assert set(dir_mtime) == find_dir_mtime
    assert cached_match == match

    # recusvie False test
    # -------------------
    find_dir_mtime = {native('test/basic/')}
    recursive = False
    match = {
            'DEFINE': ('basic',
                       'test/basic/__init__.py',
                       ('DEFINE',
                        're_import')),
            'one': ('basic.one',
                    'test/basic/one.py',
                    ('one',)),
            're_import': ('basic',
                          'test/basic/__init__.py',
                          ('DEFINE',
                           're_import')),
            'two': ('basic.two',
                    'test/basic/two.py',
                    ('two',))
           }
    match = {k: (module, native(path), variables) for k, (module, path, variables) in match.items()}
    cached_match = {}
    info, dir_mtime = prep_package('basic', pkg_path, recursive, exclude_file, exclude_dir)
    for k, v in info.items():
        cached_match[k] = v[0:3]  # note: ignore the last file modification time.
    assert cached_match == match
    assert set(dir_mtime) == find_dir_mtime


def test_prep_variables(tmp_dir):
    pkg_path = tmp_dir / 'no_pkg'
    pkg_path.mkdir()
    file_so = pkg_path / f'file{EXT_SUFFIX[1]}'
    file_so.write_text('')
    with pytest.raises(ModuleNotFoundError, match="No module named 'no_pkg'"):
        list(prep_variables('no_pkg', str(file_so)))
    assert list(prep_variables('pkg', 'file.bad')) == []
