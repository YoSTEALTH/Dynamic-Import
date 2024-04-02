from dynamic_import.record import add_record


def test_add_record(tmp_dir):
    pkg_name = 'pkg'
    cache_path = tmp_dir / f'site-packages/{pkg_name}/__pycache__/__init__.importer-313.pyc'
    record_dir = tmp_dir / 'site-packages'
    record_dir.mkdir()
    record_dir /= f'{pkg_name}-123.45.6.dist-info/'
    record_dir.mkdir()

    record_file = record_dir / 'RECORD'
    record_file.write_text('')

    add_record(pkg_name, str(cache_path))
    with open(record_file, 'rb') as file:
        assert file.read() == b'pkg/__pycache__/__init__.importer-313.pyc,,\r\n'

    # try again, shouldn't change since cache path alrady exists.
    add_record(pkg_name, str(cache_path))
    with open(record_file, 'rb') as file:
        assert file.read() == b'pkg/__pycache__/__init__.importer-313.pyc,,\r\n'
