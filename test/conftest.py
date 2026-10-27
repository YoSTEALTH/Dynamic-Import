import os
import pytest


def native(path):
    ''' Path written with '/' in a test, as `os.path` builds it on this system.

        Type
            path:   str
            return: str

        Example
            >>> native('test/basic/')
            'test/basic/'        # Windows: 'test\\basic\\'
    '''
    return path.replace('/', os.sep)


INIT = 'from dynamic_import import importer\nimporter()\n'


@pytest.fixture
def make_pkg(tmp_path, monkeypatch):
    ''' Create a throw-away package in its own holder directory and put the holder on `sys.path`.

        Type
            name:   str
            files:  dict[str, str | bytes]   e.g: {'mod.py': '...', 'sub/mod.py': '...'}
            return: pathlib.Path             package directory

        Example
            >>> def test_my_function(make_pkg):
            ...     make_pkg('my_pkg', {'mod.py': 'one = 1\n'})
            ...     from my_pkg import one

        Note
            - `__init__.py` defaults to calling `importer()`, pass your own to override it.
            - `sys.path` is restored after the test, `sys.modules` is not: use a unique package name per test.
    '''
    def make(name, files):
        holder = tmp_path / f'{name}_holder'
        pkg = holder / name
        for rel, data in ({'__init__.py': INIT} | files).items():
            path = pkg / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(data, bytes):
                path.write_bytes(data)
            else:
                path.write_text(data)
        monkeypatch.syspath_prepend(str(holder))
        return pkg
    return make
