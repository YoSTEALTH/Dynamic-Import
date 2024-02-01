import re
import pytest
from dynamic_import.check import IMPORTER_CALLED, importer_called, exclude_dir_check, exclude_file_check
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


def test_exclude_file_check(tmp_dir):
    pkg_name = 'pkg'
    pkg_dir = tmp_dir / pkg_name
    pkg_path = f'{str(pkg_dir)}/'
    file_path = pkg_dir / 'file.py'

    error = re.escape("`importer(exclude_file)` received absolute path '/file.py' must be relative path.")
    with pytest.raises(ValueError, match=error):
        exclude_file_check('/file.py', pkg_name, pkg_path)

    sup = ', '.join(EXT_SUFFIX)
    error = re.escape(f"`importer(exclude_file)` received extension '.bad' not supported. Only allowed: {sup!r}")
    with pytest.raises(ValueError, match=error):
        exclude_file_check('file.bad', pkg_name, pkg_path)

    error = re.escape(f"`importer(exclude_file)` received {str(file_path)!r} which is not an file or does not exist!")
    with pytest.raises(ValueError, match=error):
        exclude_file_check('file.py', pkg_name, pkg_path)

    pkg_dir.mkdir()           # create dir
    file_path.write_text('')  # create file

    r = exclude_file_check('file.py', pkg_name, pkg_path)
    assert isinstance(r, list)
    assert r == [str(file_path)]
    assert exclude_file_check('./file.py', pkg_name, pkg_path) == [str(file_path)]
    assert exclude_file_check(None, pkg_name, pkg_path) == []


def test_exclude_dir_check(tmp_dir):
    pkg_name = 'pkg'
    pkg_dir = tmp_dir / pkg_name
    pkg_path = f'{str(pkg_dir)}/'
    recursive = True
    sub_dir = pkg_dir / 'sub-dir/'
    sub_sub_dir = pkg_dir / 'sub/sub-dir/'

    error = re.escape("`importer(exclude_dir)` received absolute path '/sub-dir' must be relative path.")
    with pytest.raises(ValueError, match=error):
        exclude_dir_check('/sub-dir', pkg_path, recursive)

    sub = f'{tmp_dir}/sub-dir/'
    error = re.escape(f"`importer(exclude_dir)` can not find directory {sub!r} within {pkg_path!r}")
    with pytest.raises(ValueError, match=error):
        exclude_dir_check('../sub-dir', pkg_path, recursive)

    error = re.escape(f"`importer(exclude_dir)` can not find directory: '{sub_dir}/'")
    with pytest.raises(ValueError, match=error):
        exclude_dir_check('sub-dir', pkg_path, recursive)

    # prep
    pkg_dir.mkdir()
    sub_dir.mkdir()
    sub = pkg_dir / 'sub'
    sub.mkdir()
    sub_sub_dir.mkdir()
    IMPORTER_CALLED[pkg_path] = set()

    # single
    assert exclude_dir_check('sub-dir', pkg_path, recursive) == [f'{sub_dir}/']
    # multiple
    assert exclude_dir_check(('sub-dir', 'sub/sub-dir'), pkg_path, recursive) == [f'{sub_dir}/', f'{sub_sub_dir}/']
    # holder
    assert IMPORTER_CALLED[pkg_path] == {f'{sub_dir}/', f'{sub_sub_dir}/'}
