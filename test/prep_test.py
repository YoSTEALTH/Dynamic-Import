import pytest
from dynamic_import.prep import EXT_SUFFIX, prep_package, prep_variables


def test_cache():
    assert isinstance(EXT_SUFFIX, tuple)
    suffix = iter(EXT_SUFFIX)
    assert next(suffix) == '.py'
    cpython = next(suffix)
    assert cpython.startswith('.cpython-') and cpython.endswith('.so')
    assert next(suffix) == '.abi3.so'


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
