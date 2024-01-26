import re
import pytest
from dynamic_import.check import IMPORTER_CALLED, importer_called, exclude_dir_check, exclude_file_check
from dynamic_import.prep import EXT_SUFFIX


def test_importer_called(tmpdir):
    pkg_path = '/path/pkg/'
    assert isinstance(IMPORTER_CALLED, dict)
    assert IMPORTER_CALLED.get(pkg_path, None) is None
    importer_called(pkg_path)
    assert isinstance(IMPORTER_CALLED.get(pkg_path, None), set)

    # error
    with pytest.raises(ImportError):
        importer_called(pkg_path)


def test_exclude_file_check(tmpdir):
    pkg_name = 'pkg'
    pkg_dir = tmpdir / pkg_name
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

    pkg_dir.mkdir()       # create dir
    file_path.write(b'')  # create file

    r = exclude_file_check('file.py', pkg_name, pkg_path)
    assert isinstance(r, list)
    assert r == [file_path]
    assert exclude_file_check('./file.py', pkg_name, pkg_path) == [file_path]
    assert exclude_file_check(None, pkg_name, pkg_path) == []


def test_exclude_dir_check(tmpdir):
    pkg_name = 'pkg'
    pkg_dir = tmpdir / pkg_name
    pkg_path = f'{str(pkg_dir)}/'
    recursive = True
    sub_dir = pkg_dir / 'sub-dir/'
    sub_sub_dir = pkg_dir / 'sub/sub-dir/'

    error = re.escape("`importer(exclude_dir)` received absolute path '/sub-dir' must be relative path.")
    with pytest.raises(ValueError, match=error):
        exclude_dir_check('/sub-dir', pkg_path, recursive)

    sub = f'{tmpdir}/sub-dir/'
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
