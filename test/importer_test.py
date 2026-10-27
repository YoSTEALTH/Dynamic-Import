import os
import re
import sys
import threading
import pytest
from dynamic_import.cache import pkg_cache_path


def test_sub_module_registered_once(make_pkg):
    # 2.1: lazily loaded sub-module lands in `sys.modules`, a later absolute import must not run it again.
    make_pkg('reg_pkg', {'sub/mod.py': 'class Thing:\n    pass\n\ndef make():\n    return Thing()\n'})
    from reg_pkg import Thing, make
    assert 'reg_pkg.sub.mod' in sys.modules
    assert 'reg_pkg.sub' in sys.modules  # parent (namespace) package imported as well
    import reg_pkg.sub.mod as mod
    assert mod.Thing is Thing
    assert isinstance(make(), mod.Thing)
    from reg_pkg.sub import mod as mod2
    assert mod2 is mod
    assert sys.modules['reg_pkg.sub'].mod is mod


def test_failed_sub_module_not_registered(make_pkg):
    make_pkg('fail_pkg', {'bad.py': 'x = 1\nraise RuntimeError("boom")\n'})
    import fail_pkg
    with pytest.raises(RuntimeError, match='boom'):
        fail_pkg.x
    assert 'fail_pkg.bad' not in sys.modules


def test_all_name_not_defined(make_pkg):
    # 2.5: clear error instead of a misleading `cannot import name`
    make_pkg('missing_pkg', {'mod.py': '__all__ = ("real", "ghost")\nreal = 1\n'})
    import missing_pkg
    error = re.escape("cannot import name 'ghost' from 'missing_pkg.mod' (") + '.*mod.py' + \
        re.escape("): it is listed in `__all__` but the module does not define it.")
    with pytest.raises(ImportError, match=error):
        missing_pkg.real


def test_thread_safe(tmp_dir, make_pkg):
    # 2.6: many threads asking for the same name execute the sub-module exactly once.
    marker = tmp_dir / 'runs.txt'
    code = f'import time\nwith open({str(marker)!r}, "a") as f:\n    f.write("x")\ntime.sleep(0.05)\nvalue = 42\n'
    make_pkg('thread_pkg', {'slow.py': code})
    import thread_pkg

    results = []
    threads = [threading.Thread(target=lambda: results.append(thread_pkg.value)) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert results == [42] * 8
    assert marker.read_text() == 'x'


def test_init_runs_once(tmp_dir, make_pkg):
    # 2.9: `__init__.py` is never executed a second time, names defined after `importer()` are read lazily.
    marker = tmp_dir / 'init_runs.txt'
    init = 'from dynamic_import import importer\nimporter()\n' \
           f'with open({str(marker)!r}, "a") as f:\n    f.write("x")\nafter = 2\n'
    make_pkg('once_pkg', {'__init__.py': init, 'mod.py': 'lazy = 1\n'})
    import once_pkg
    from once_pkg import after, lazy
    assert (lazy, after) == (1, 2)
    assert once_pkg.after == 2
    import once_pkg.mod  # noqa
    assert marker.read_text() == 'x'


def test_not_recursive_parent_and_sub_importer(make_pkg):
    # 2.2: `importer(recursive=False)` in the parent, `importer()` in a sub-package.
    make_pkg('flat_pkg', {'__init__.py': 'from dynamic_import import importer\nimporter(recursive=False)\n',
                          'top.py': 'top = 1\n',
                          'sub/__init__.py': 'from dynamic_import import importer\nimporter()\n',
                          'sub/deep.py': 'deep = 2\n'})
    from flat_pkg import top
    assert top == 1
    with pytest.raises(ImportError):
        from flat_pkg import deep  # noqa - not scanned
    from flat_pkg.sub import deep
    assert deep == 2


def test_sub_importer_called_first(make_pkg):
    # 2.8: parent imports the sub-package (which calls `importer()`) before calling `importer()` itself.
    make_pkg('order_pkg', {'__init__.py': 'from . import sub\nfrom dynamic_import import importer\nimporter()\n',
                           'sub/__init__.py': 'from dynamic_import import importer\nimporter()\n',
                           'sub/deep.py': 'deep = 2\n'})
    with pytest.raises(ImportError, match=re.escape("previously called from sub-directory")):
        import order_pkg  # noqa


def test_tuple_assignment(make_pkg):
    # 1.1: module-level tuple/attribute/subscript assignments do not crash the scan.
    code = 'import os\nx, y = 1, 2\nos.environ["DI_TEST"] = "1"\nos.environ.__dict__["z"] = 1\na: int = 3\nb: int\n'
    make_pkg('tuple_pkg', {'mod.py': code})
    from tuple_pkg import a, x, y
    assert (x, y, a) == (1, 2, 3)
    with pytest.raises(ImportError):
        from tuple_pkg import b  # noqa - annotation only


@pytest.mark.skipif(sys.platform == 'win32' or os.getuid() == 0,
                    reason='root ignores directory permissions, Windows ignores read-only on directories')
def test_read_only_package(make_pkg):
    # 1.3: cache directory can not be created, `importer()` must still work.
    pkg = make_pkg('ro_pkg', {'mod.py': 'ro = True\n'})
    os.chmod(pkg, 0o555)
    try:
        from ro_pkg import ro
        assert ro is True
        assert not os.path.exists(pkg_cache_path(os.path.join(pkg, ''), '__init__.py', 'importer'))
    finally:
        os.chmod(pkg, 0o755)


def test_pycache_prefix(tmp_dir, make_pkg, monkeypatch):
    # 1.2: with `sys.pycache_prefix` every package gets its own cache file under the prefix.
    prefix = tmp_dir / 'prefix' / 'deeper'  # parent does not exist yet
    monkeypatch.setattr(sys, 'pycache_prefix', str(prefix))
    pkg_a = make_pkg('prefix_a', {'mod.py': 'alpha = 1\n'})
    pkg_b = make_pkg('prefix_b', {'mod.py': 'beta = 2\n'})
    from prefix_a import alpha
    from prefix_b import beta
    assert (alpha, beta) == (1, 2)
    with pytest.raises(ImportError):
        from prefix_b import alpha  # noqa - must not see package A's cache

    cache_a = pkg_cache_path(os.path.join(pkg_a, ''), '__init__.py', 'importer')
    cache_b = pkg_cache_path(os.path.join(pkg_b, ''), '__init__.py', 'importer')
    assert cache_a != cache_b
    assert cache_a.startswith(str(prefix)) and cache_a.endswith(f'{os.sep}prefix_a{os.sep}__init__.importer-' +
                                                                 cache_a.rsplit('-', 1)[1])
    assert os.path.exists(cache_a) and os.path.exists(cache_b)
    assert not os.path.exists(pkg_a / '__pycache__')
