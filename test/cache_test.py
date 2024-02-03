import os
import sys
import os.path
import time
import shutil
import pytest
from dynamic_import.version import version
from dynamic_import.cache import CACHE_DIR_PATH, MARSHAL_VERSION, VERSION_TAG, CACHE_EXT, \
                                 pkg_cache_path, dump_cache, load_cache, create_cache_dir


def test_pkg_cache_path(tmp_path):
    func_name = 'importer'
    pkg_name = 'pkg'
    pkg_path = f'{str(tmp_path / pkg_name)}/'
    assert pkg_cache_path(pkg_path, '__init__.py', func_name) == str(
        tmp_path / pkg_name / f'__pycache__/__init__.{func_name}-{VERSION_TAG}{CACHE_EXT}')
    assert pkg_cache_path(pkg_path, 'in.py', func_name) == str(
        tmp_path / pkg_name / f'__pycache__/in.{func_name}-{VERSION_TAG}{CACHE_EXT}')


def test_defines():
    assert CACHE_DIR_PATH == '__pycache__'
    assert MARSHAL_VERSION == 4


def test_dump_load(tmp_dir):
    recursive = True
    exclude_dir = []
    exclude_file = []

    tmp_one = tmp_dir / 'one.py'
    tmp_one.write_text('hello ')

    dir_mtime = {str(tmp_dir): os.stat(tmp_dir).st_mtime}
    info = {'one': ('a', str(tmp_one), ('a', 'b', 'c'), os.stat(tmp_one).st_mtime)}
    cache_file = pkg_cache_path(tmp_dir, '__init__.py', 'importer')

    assert create_cache_dir(cache_file) is True
    assert dump_cache(cache_file, info, recursive, exclude_file, exclude_dir, dir_mtime, version) is None

    # Exception
    assert load_cache('bad-file', recursive, exclude_file, exclude_dir, version) is None

    # version != cached_version
    assert load_cache(cache_file, recursive, exclude_file, exclude_dir, 123.45) is None

    # exclude_file != cached_exclude_file
    assert load_cache(cache_file, recursive, ['two'], [str(tmp_dir / 'two')], version) is None

    # exclude_dir != cached_exclude_dir
    assert load_cache(cache_file, recursive, exclude_file, [str(tmp_dir / 'two')], version) is None

    # recursive != cached_recursive
    assert load_cache(cache_file, False, exclude_file, exclude_dir, version) is None

    # mtime != mtime_it(file_path)
    time.sleep(0.05)  # need some time delay for stat meta to catch up.
    tmp_one.write_text('world')  # write again so modified time changes.
    assert load_cache(cache_file, recursive, exclude_file, exclude_dir, version) is None

    # mtime != mtime_it(dir_path)
    time.sleep(0.05)
    # check if dir time as changed by adding a file
    empty_file = tmp_dir / 'empty_file.ext'
    empty_file.write_text('')
    assert load_cache(cache_file, recursive, exclude_file, exclude_dir, version) is None


def test_define():
    from basic import DEFINE
    assert DEFINE == 123

    from basic import re_import
    assert re_import() is None

    import basic
    assert basic.DEFINE == 123
    assert basic.re_import() is None


def test_conflict():
    with pytest.raises(ImportError):
        from basic import does_not_exist  # noqa


def test_dynamic(tmp_dir):
    # part-1
    # ------
    pkg_name = 'dynamic_pkg'
    pkg_dir = tmp_dir / 'holder'
    pkg_dir.mkdir()
    # tmp_init = pkg_dir / '__init__.py'
    # tmp_init.write(b'')

    pkg_path = pkg_dir / f'{pkg_name}/'
    pkg_path.mkdir()

    init_path = pkg_dir / pkg_name / '__init__.py'
    # cache enabled
    init_path.write_text('from dynamic_import import importer\nimporter(cache=True)\n')

    one_path = pkg_dir / pkg_name / 'one.py'
    one_path.write_text('ONE = 1\n')

    sys.path.append(str(pkg_dir))
    from dynamic_pkg import ONE
    assert ONE == 1

    # part-2
    # ------
    # cache disabled
    init_path.write_text('from dynamic_import import importer\nimporter(cache=False)\n')

    # copy into new folder
    new_pkg_dir = tmp_dir / 'new_holder'
    old_pkg_path = new_pkg_dir / f'{pkg_name}/'
    new_pkg_path = new_pkg_dir / f'new_{pkg_name}/'

    shutil.copytree(pkg_dir, new_pkg_dir)
    os.rename(old_pkg_path, new_pkg_path)

    sys.path.append(str(new_pkg_dir))
    from new_dynamic_pkg import ONE
    assert ONE == 1
