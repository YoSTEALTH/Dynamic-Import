import os
import os.path
import pytest
from dynamic_import.cache import CACHE_DIR_PATH, MARSHAL_VERSION, VERSION_TAG, CACHE_EXT, pkg_cache_path, \
                      dump_cache, load_cache, create_cache_dir


def test_pkg_cache_path(tmpdir):
    name = 'importer'
    tmp_one = tmpdir.join('__init__.py')
    tmp_two = tmpdir.join('in.py')
    assert pkg_cache_path(tmp_one, name) == tmpdir.join(f'__pycache__/__init__.{name}-{VERSION_TAG}{CACHE_EXT}')
    assert pkg_cache_path(tmp_two, name) == tmpdir.join(f'__pycache__/in.{name}-{VERSION_TAG}{CACHE_EXT}')


def test_defines():
    assert CACHE_DIR_PATH == '__pycache__'
    assert MARSHAL_VERSION == 4


def test_dump_load(tmpdir, tmp_path):
    # version = '0123.45.67'
    recursive = True
    exclude_paths = []

    tmp_one = tmp_path / 'one.py'
    tmp_one.write_text('')
    dir_mtime = {str(tmpdir): os.stat(tmpdir).st_mtime}

    info = {'one': ('a', str(tmp_one), ('a', 'b', 'c'), os.stat(tmp_one).st_mtime)}
    tmp_file = pkg_cache_path(os.path.join(tmpdir, '__init__.py'), 'importer')
    assert create_cache_dir(tmp_file) is True
    assert dump_cache(tmp_file, info, recursive, exclude_paths, dir_mtime) is None

    assert load_cache(tmp_file, recursive, [tmp_path / 'two']) is None
    assert load_cache(tmp_file, False, exclude_paths) is None
    assert load_cache(tmp_file, recursive, exclude_paths) == info


def test_blocking():
    with pytest.raises(ValueError, match="special name like '__block__' is not supported"):
        from block import __block__  # noqa

    with pytest.raises(ValueError, match="special name like '__block1__' is not supported"):
        from block1 import __block1__  # noqa


def test_define():
    from basic import DEFINE
    assert DEFINE == 123


def test_lur_cache():
    import basic
    # check for lur_cache
    basic.re_import()
    basic.re_import()
    basic.re_import()
    basic.re_import()

    from basic import re_import
    # check for lur_cache
    re_import()
    re_import()
    re_import()
    re_import()


def test_conflict():
    with pytest.raises(ImportError):
        from basic import does_not_exist  # noqa


# import os
# import os.path
# import random
# from dynamic_import.cache import TEMP_DIR_PATH, MARSHAL_VERSION, cache_pkg_path, \
#                            dump_cache, load_cache


# def test_defines():
#     assert TEMP_DIR_PATH.endswith('/importer-for-python')
#     assert MARSHAL_VERSION == 4


# def test_cache_file_path():
#     pkg_file = '/pkg/__init__.py'
#     match_hash = os.path.join(TEMP_DIR_PATH, f'2895055407.{os.getuid()}')
#     assert cache_pkg_path(pkg_file) == match_hash


# def test_dump_load(tmpdir):
#     info = {'one': random.random(), 'sub': ('two', 'three')}
#     tmp_file = tmpdir.join('0437265142b5344a415e23acb7c14e0e')
#     assert dump_cache(tmp_file, info) is None
#     assert load_cache(tmp_file) == info
#     os.remove(tmp_file)
