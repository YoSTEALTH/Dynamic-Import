import sys
from dynamic_import.prep import EXT_SUFFIX, prep_package


def test_cache():
    assert isinstance(EXT_SUFFIX, tuple)
    suffix = iter(EXT_SUFFIX)
    assert next(suffix) == '.py'
    cpython = next(suffix)
    assert cpython.startswith('.cpython-') and cpython.endswith('.so')
    assert next(suffix) == '.abi3.so'


def test_prep():
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
    find_dir_mtime = {'test/basic', 'test/basic/sub', 'test/basic/sub/conflict', 'test/basic/sub/child'}
    cached_match = {}
    info, dir_mtime = prep_package('test/basic/__init__.py', True)
    for k, v in info.items():
        cached_match[k] = v[0:3]  # note: ignore the last file modification time.

    assert dir_mtime.keys() == find_dir_mtime
    assert cached_match == match
    assert 'html' not in sys.modules
