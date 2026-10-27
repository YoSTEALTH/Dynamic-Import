import re
import sys
import pytest
from os.path import join
from conftest import native
from dynamic_import.check import IMPORTER_CALLED, importer_called, is_rooted, exclude_dir_check, exclude_file_check
from dynamic_import.prep import EXT_SUFFIX


def test_importer_called():
    pkg_path = '/path/pkg/'
    assert isinstance(IMPORTER_CALLED, dict)
    assert IMPORTER_CALLED.get(pkg_path, None) is None
    assert importer_called(pkg_path) is None
    assert isinstance(IMPORTER_CALLED.get(pkg_path, None), set)

    # calling `importer()` again!
    assert importer_called(pkg_path) is True

    # calling `importer()` from sub directory while it was previously declared on higher path!
    pkg_path = '/path/pkg/sub/pkg/'
    with pytest.raises(ImportError):
        importer_called(pkg_path)

    # exclude
    pkg_path1 = '/path/new_pkg/sub_dir/sub_1/'
    pkg_path2 = '/path/new_pkg/sub_dir/'
    IMPORTER_CALLED[pkg_path2] = {'/path/new_pkg/sub_dir/sub_1/'}
    assert importer_called(pkg_path1) is None
    assert IMPORTER_CALLED[pkg_path1] == set()

    # `exclude_dir` is recorded
    assert importer_called('/path/excl/', True, ['/path/excl/sub/']) is None
    assert IMPORTER_CALLED['/path/excl/'] == {'/path/excl/sub/'}
    assert importer_called('/path/excl/sub/') is None


def test_importer_called_not_recursive():
    # parent with `recursive=False` never scanned the sub-directory, so sub-package may call `importer()`
    assert importer_called('/path/flat/', recursive=False) is None
    assert IMPORTER_CALLED['/path/flat/'] is None
    assert importer_called('/path/flat/sub/') is None
    assert importer_called('/path/flat/', recursive=False) is True  # called again
    assert importer_called('/path/flat/sub/') is True


def test_importer_called_sub_first():
    # sub-directory called `importer()` before the parent
    assert importer_called('/path/top/sub/') is None
    with pytest.raises(ImportError, match=re.escape("previously called from sub-directory '/path/top/sub/'")):
        importer_called('/path/top/')
    assert '/path/top/' not in IMPORTER_CALLED
    # ... fine if parent excludes it or is not recursive
    assert importer_called('/path/top/', True, ['/path/top/sub/']) is None
    assert importer_called('/path/top2/sub/') is None
    assert importer_called('/path/top2/', recursive=False) is None


def test_is_rooted():
    assert is_rooted('/file.py') and is_rooted(native('/file.py'))
    assert not any(map(is_rooted, ('file.py', 'sub/file.py', './file.py', native('sub/file.py'))))
    if sys.platform == 'win32':  # 3.13+: `isabs()` is `False` for these, `join()` still leaves the package
        assert is_rooted('C:file.py') and is_rooted('C:\\pkg\\file.py') and is_rooted('\\file.py')


def test_exclude_file_check(tmp_dir):
    pkg_name = 'pkg'
    pkg_dir = tmp_dir / pkg_name
    pkg_path = join(pkg_dir, '')
    file_path = pkg_dir / 'file.py'

    error = re.escape("`importer(exclude_file)` received absolute path '/file.py' must be relative path.")
    with pytest.raises(ValueError, match=error):
        exclude_file_check('/file.py', pkg_path)

    sup = ', '.join(EXT_SUFFIX)
    error = re.escape(f"`importer(exclude_file)` received extension '.bad' not supported. Only allowed: {sup!r}")
    with pytest.raises(ValueError, match=error):
        exclude_file_check('file.bad', pkg_path)

    error = re.escape(f"`importer(exclude_file)` received {str(file_path)!r} which is not an file or does not exist!")
    with pytest.raises(ValueError, match=error):
        exclude_file_check('file.py', pkg_path)

    pkg_dir.mkdir()           # create dir
    file_path.write_text('')  # create file

    r = exclude_file_check('file.py', pkg_path)
    assert isinstance(r, list)
    assert r == [str(file_path)]
    assert exclude_file_check('./file.py', pkg_path) == [str(file_path)]
    assert exclude_file_check(None, pkg_path) == []


def test_exclude_dir_check(tmp_dir):
    pkg_name = 'pkg'
    pkg_dir = tmp_dir / pkg_name
    pkg_path = join(pkg_dir, '')
    recursive = True
    sub_dir = pkg_dir / 'sub-dir/'
    sub_sub_dir = pkg_dir / 'sub/sub-dir/'

    error = re.escape("`importer(exclude_dir)` received absolute path '/sub-dir' must be relative path.")
    with pytest.raises(ValueError, match=error):
        exclude_dir_check('/sub-dir', pkg_path, recursive)

    sub = join(tmp_dir, 'sub-dir', '')
    error = re.escape(f"`importer(exclude_dir)` can not find directory {sub!r} within {pkg_path!r}")
    with pytest.raises(ValueError, match=error):
        exclude_dir_check('../sub-dir', pkg_path, recursive)

    error = re.escape(f"`importer(exclude_dir)` can not find directory: {join(sub_dir, '')!r}")
    with pytest.raises(ValueError, match=error):
        exclude_dir_check('sub-dir', pkg_path, recursive)

    # prep
    pkg_dir.mkdir()
    sub_dir.mkdir()
    sub = pkg_dir / 'sub'
    sub.mkdir()
    sub_sub_dir.mkdir()

    # single
    assert exclude_dir_check('sub-dir', pkg_path, recursive) == [join(sub_dir, '')]
    # multiple
    assert exclude_dir_check(('sub-dir', 'sub/sub-dir'), pkg_path, recursive) == [join(sub_dir, ''),
                                                                                  join(sub_sub_dir, '')]
    # not recursive: nothing to exclude
    assert exclude_dir_check(('sub-dir', 'sub/sub-dir'), pkg_path, False) == []
    assert exclude_dir_check(None, pkg_path, recursive) == []
