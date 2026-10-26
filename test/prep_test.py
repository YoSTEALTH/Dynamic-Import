import pytest
from dynamic_import.prep import EXT_SUFFIX, prep_package, prep_variables


def test_cache():
    assert isinstance(EXT_SUFFIX, tuple)
    suffix = iter(EXT_SUFFIX)
    assert next(suffix) == '.py'
    cpython = next(suffix)
    assert cpython.startswith('.cpython-') and cpython.endswith('.so')
    abi3 = next(suffix)  # '.abi3.so', 3.15+: '.abi3-x86_64-linux-gnu.so' or '.abi3t-...'
    assert abi3.startswith('.abi3') and abi3.endswith('.so')
    assert '.so' not in EXT_SUFFIX  # bundled `libfoo.so` must not be treated as a module


def test_prep_data_dir(tmp_dir):
    # a directory without any module is still tracked, so a module added later invalidates the cache.
    pkg_path = tmp_dir / 'pkg'
    pkg_path.mkdir()
    (pkg_path / '__init__.py').write_text('')
    (pkg_path / 'data').mkdir()
    (pkg_path / 'data' / 'file.txt').write_text('')
    (pkg_path / 'data' / 'libfoo.so').write_text('')  # shared library, not a module
    (pkg_path / '__pycache__').mkdir()
    (pkg_path / '__pycache__' / 'x.py').write_text('')
    (pkg_path / 'skip').mkdir()
    (pkg_path / 'skip' / 'deep').mkdir()
    (pkg_path / 'skip' / 'deep' / 'mod.py').write_text('x = 1')

    info, dir_mtime = prep_package('pkg', f'{pkg_path}/', True, [], [f'{pkg_path}/skip/'])
    assert info == {}
    assert set(dir_mtime) == {f'{pkg_path}/', f'{pkg_path}/data/'}  # `__pycache__` and `skip/` not descended

    (pkg_path / 'data' / 'mod.py').write_text('x = 1')
    info, _ = prep_package('pkg', f'{pkg_path}/', True, [], [])
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
    find_dir_mtime = {'test/basic/',
                      'test/basic/so/',
                      'test/basic/sub/',
                      'test/basic/sub/conflict/',
                      'test/basic/sub/child/'}
    cached_match = {}
    recursive = True
    pkg_path = 'test/basic/'

    exclude_file = ['test/basic/sub/skip-me.py']
    exclude_dir = ['test/basic/skip/']

    info, dir_mtime = prep_package('basic', pkg_path, recursive, exclude_file, exclude_dir)
    for k, v in info.items():
        cached_match[k] = v[0:3]  # note: ignore the last file modification time.

    assert set(dir_mtime) == find_dir_mtime
    assert cached_match == match

    # recusvie False test
    # -------------------
    find_dir_mtime = {'test/basic/'}
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
