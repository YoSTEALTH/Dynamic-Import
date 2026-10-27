import marshal
import os
import os.path
import shutil
import sys
import time
from os.path import join
import pytest
from conftest import native
from dynamic_import.cache import (
    CACHE_DIR_PATH,
    CACHE_EXT,
    MARSHAL_VERSION,
    VERSION_TAG,
    create_cache_dir,
    dump_cache,
    load_cache,
    pkg_cache_path,
)
from dynamic_import.version import version


def test_pkg_cache_path(tmp_path):
    func_name = 'importer'
    pkg_name = 'pkg'
    pkg_path = join(tmp_path / pkg_name, '')
    assert pkg_cache_path(pkg_path, '__init__.py', func_name) == str(
        tmp_path / pkg_name / f'__pycache__/__init__.{func_name}-{VERSION_TAG}{CACHE_EXT}')
    assert pkg_cache_path(pkg_path, 'in.py', func_name) == str(
        tmp_path / pkg_name / f'__pycache__/in.{func_name}-{VERSION_TAG}{CACHE_EXT}')


def test_pkg_cache_path_prefix(monkeypatch):
    name = f'__init__.importer-{VERSION_TAG}{CACHE_EXT}'
    monkeypatch.setattr(sys, 'pycache_prefix', native('/tmp/pyc'))
    assert pkg_cache_path(native('/path/pkg/'), '__init__.py', 'importer') == native(f'/tmp/pyc/path/pkg/{name}')
    if sys.platform == 'win32':  # drive is dropped like `cache_from_source()` does
        monkeypatch.setattr(sys, 'pycache_prefix', 'C:\\pyc')
        assert pkg_cache_path('D:\\path\\pkg\\', '__init__.py', 'importer') == f'C:\\pyc\\path\\pkg\\{name}'
    monkeypatch.setattr(sys, 'pycache_prefix', None)
    assert pkg_cache_path(native('/path/pkg/'), '__init__.py', 'importer') == native(f'/path/pkg/__pycache__/{name}')


def test_create_cache_dir_nested(tmp_path):
    cache_file = str(tmp_path / 'a/b/c/__init__.importer-313.pyc')
    assert create_cache_dir(cache_file) is None
    assert os.path.isdir(tmp_path / 'a/b/c')
    assert create_cache_dir(cache_file) is None  # already exists, no error


def test_defines():
    assert CACHE_DIR_PATH == '__pycache__'
    assert MARSHAL_VERSION == 4


def test_dump_load(tmp_path):
    recursive = True
    exclude_dir = []
    exclude_file = []

    tmp_one = tmp_path / 'one.py'
    tmp_one.write_text('hello ')

    dir_mtime = {str(tmp_path): os.stat(tmp_path).st_mtime}
    info = {'one': ('a', str(tmp_one), ('a', 'b', 'c'), os.stat(tmp_one).st_mtime)}
    cache_file = pkg_cache_path(tmp_path, '__init__.py', 'importer')

    assert create_cache_dir(cache_file) is None
    assert dump_cache(cache_file, info, recursive, exclude_file, exclude_dir, dir_mtime, version) is None

    # Exception
    assert load_cache('bad-file', recursive, exclude_file, exclude_dir, version) is None

    # version != cached_version
    assert load_cache(cache_file, recursive, exclude_file, exclude_dir, 123.45) is None

    # exclude_file != cached_exclude_file
    assert load_cache(cache_file, recursive, ['two'], [str(tmp_path / 'two')], version) is None

    # exclude_dir != cached_exclude_dir
    assert load_cache(cache_file, recursive, exclude_file, [str(tmp_path / 'two')], version) is None

    # recursive != cached_recursive
    assert load_cache(cache_file, False, exclude_file, exclude_dir, version) is None

    # mtime != mtime_it(file_path)
    time.sleep(0.05)  # need some time delay for stat meta to catch up.
    tmp_one.write_text('world')  # write again so modified time changes.
    assert load_cache(cache_file, recursive, exclude_file, exclude_dir, version) is None

    # mtime != mtime_it(dir_path)
    time.sleep(0.05)
    # check if dir time as changed by adding a file
    empty_file = tmp_path / 'empty_file.ext'
    empty_file.write_text('')
    assert load_cache(cache_file, recursive, exclude_file, exclude_dir, version) is None


def test_dump_atomic(tmp_path):
    # 2.18: written through a temporary file, which is removed if the write fails.
    cache_file = str(tmp_path / 'cache.pyc')
    dump_cache(cache_file, {'one': 0}, True, [], [], {}, version)
    dump_cache(cache_file, {'one': 1}, True, [], [], {}, version)  # replaces the existing file
    assert os.listdir(tmp_path) == ['cache.pyc']
    with pytest.raises(ValueError):
        dump_cache(cache_file, {'one': object()}, True, [], [], {}, version)  # `marshal` can not write it
    assert os.listdir(tmp_path) == ['cache.pyc']
    with open(cache_file, 'rb') as file:
        assert marshal.load(file)[-1] == {'one': 1}  # last good cache left intact


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


def test_dynamic(make_pkg, monkeypatch):
    # cache enabled
    pkg = make_pkg('dynamic_pkg', {'__init__.py': 'from dynamic_import import importer\nimporter(cache=True)\n',
                                   'one.py': 'ONE = 1\n'})
    from dynamic_pkg import ONE
    assert ONE == 1
    cache_file = pkg_cache_path(join(pkg, ''), '__init__.py', 'importer')
    assert os.path.exists(cache_file)

    # copy (old cache file included) into a renamed package with cache disabled
    new_pkg = pkg.parent.parent / 'new_holder' / 'new_dynamic_pkg'
    shutil.copytree(pkg, new_pkg)
    (new_pkg / '__init__.py').write_text('from dynamic_import import importer\nimporter(cache=False)\n')
    monkeypatch.syspath_prepend(str(new_pkg.parent))
    from new_dynamic_pkg import ONE
    assert ONE == 1
    assert not os.path.exists(pkg_cache_path(join(new_pkg, ''), '__init__.py', 'importer'))  # removed
