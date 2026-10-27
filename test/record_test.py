import os
from os.path import join
from dynamic_import.record import add_record


def test_add_record(tmp_path):
    pkg_name = 'pkg'
    cache_path = tmp_path / f'site-packages/{pkg_name}/__pycache__/__init__.importer-313.pyc'
    cache_path = str(cache_path)
    record_dir = tmp_path / 'site-packages'
    record_dir.mkdir()
    record_dir /= f'{pkg_name}-123.45.6.dist-info/'
    record_dir.mkdir()

    record_file = record_dir / 'RECORD'
    record_file.write_text('')

    add_record(pkg_name, cache_path)
    with open(record_file, 'rb') as file:
        assert file.read() == b'pkg/__pycache__/__init__.importer-313.pyc,,\r\n'

    # try again, shouldn't change since cache path already exists.
    add_record(pkg_name, cache_path)
    with open(record_file, 'rb') as file:
        assert file.read() == b'pkg/__pycache__/__init__.importer-313.pyc,,\r\n'

    # test sub-module, `importer()` passes the sub-package name
    before, after = cache_path.split(f'{os.sep}{pkg_name}{os.sep}')
    cache_sub_module_path = join(before, pkg_name, 'sub_module', after)
    add_record(f'{pkg_name}.sub_module', cache_sub_module_path)
    with open(record_file, 'rb') as file:
        assert file.read() == b'pkg/__pycache__/__init__.importer-313.pyc,,\r\n' \
                              b'pkg/sub_module/__pycache__/__init__.importer-313.pyc,,\r\n'

    # not inside `site-packages`
    add_record(pkg_name, str(tmp_path / 'elsewhere/pkg/__pycache__/__init__.importer-313.pyc'))
    with open(record_file, 'rb') as file:
        assert file.read().count(b'\r\n') == 2


def test_add_record_other_dist_name(tmp_path):
    # 2.7: distribution named differently than the package, `site-packages` twice in the path,
    #      `RECORD` without trailing newline.
    site = tmp_path / 'site-packages/venv/lib/site-packages'
    site.mkdir(parents=True)
    other = site / 'Other_Dist-1.0.dist-info'
    other.mkdir()
    (other / 'RECORD').write_bytes(b'other/__init__.py,sha256=abc,10\r\n')
    owner = site / 'Real_Name-2.0.dist-info'
    owner.mkdir()
    (owner / 'RECORD').write_bytes(b'pkg/__init__.py,sha256=abc,10\r\npkg/mod.py,sha256=def,20')

    add_record('pkg.sub', str(site / 'pkg/sub/__pycache__/__init__.importer-313.pyc'))
    assert (other / 'RECORD').read_bytes() == b'other/__init__.py,sha256=abc,10\r\n'
    assert (owner / 'RECORD').read_bytes() == b'pkg/__init__.py,sha256=abc,10\r\npkg/mod.py,sha256=def,20\r\n' \
                                              b'pkg/sub/__pycache__/__init__.importer-313.pyc,,\r\n'
