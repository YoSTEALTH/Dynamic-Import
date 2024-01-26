import os
import os.path
import pytest
from dynamic_import.cache import CACHE_DIR_PATH, MARSHAL_VERSION, VERSION_TAG, CACHE_EXT, \
                                 pkg_cache_path, dump_cache, load_cache, create_cache_dir


def test_pkg_cache_path(tmpdir):
    func_name = 'importer'
    pkg_name = 'pkg'
    pkg_path = f'{str(tmpdir / pkg_name)}/'
    assert pkg_cache_path(pkg_path, '__init__.py', func_name) == str(
        tmpdir / pkg_name / f'__pycache__/__init__.{func_name}-{VERSION_TAG}{CACHE_EXT}')
    assert pkg_cache_path(pkg_path, 'in.py', func_name) == str(
        tmpdir / pkg_name / f'__pycache__/in.{func_name}-{VERSION_TAG}{CACHE_EXT}')


def test_defines():
    assert CACHE_DIR_PATH == '__pycache__'
    assert MARSHAL_VERSION == 4


def test_dump_load(tmpdir, tmp_path):
    recursive = True
    exclude_dir = []
    exclude_file = []  # TODO: need to add test for this

    tmp_one = tmp_path / 'one.py'
    tmp_one.write_text('')
    dir_mtime = {str(tmpdir): os.stat(tmpdir).st_mtime}

    info = {'one': ('a', str(tmp_one), ('a', 'b', 'c'), os.stat(tmp_one).st_mtime)}
    tmp_file = pkg_cache_path(tmpdir, '__init__.py', 'importer')

    assert create_cache_dir(tmp_file) is True
    assert dump_cache(tmp_file, info, recursive, exclude_file, exclude_dir, dir_mtime) is None

    assert load_cache(tmp_file, recursive, exclude_file, [tmp_path / 'two']) is None
    assert load_cache(tmp_file, False, exclude_file, exclude_dir) is None
    assert load_cache(tmp_file, recursive, exclude_file, exclude_dir) == info


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
