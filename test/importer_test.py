import importlib
import os
import re
import subprocess
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


def test_thread_safe(tmp_path, make_pkg):
    # 2.6: many threads asking for the same name execute the sub-module exactly once.
    marker = tmp_path / 'runs.txt'
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


def test_init_runs_once(tmp_path, make_pkg):
    # 2.9: `__init__.py` is never executed a second time, names defined after `importer()` are read lazily.
    marker = tmp_path / 'init_runs.txt'
    init = 'from dynamic_import import importer\nimporter()\n' \
           f'with open({str(marker)!r}, "a") as f:\n    f.write("x")\nafter = 2\n'
    make_pkg('once_pkg', {'__init__.py': init, 'mod.py': 'lazy = 1\n'})
    import once_pkg
    from once_pkg import after, lazy
    assert (lazy, after) == (1, 2)
    assert once_pkg.after == 2
    import once_pkg.mod  # noqa
    assert marker.read_text() == 'x'


def test_import_star(make_pkg):
    # 2.14: `from pkg import *` imports the exported names only, never the package's special names.
    init = 'from dynamic_import import importer\nimporter()\nafter = 2\n'
    make_pkg('star_pkg', {'__init__.py': init, 'mod.py': 'one = 1\n'})
    ns = {'__name__': 'caller'}
    exec('from star_pkg import *', ns)
    assert ns['__name__'] == 'caller'
    assert '__file__' not in ns and '__path__' not in ns
    assert (ns['one'], ns['after']) == (1, 2)
    import star_pkg
    assert sorted(star_pkg.__all__) == ['after', 'one']
    assert {'__name__', '__file__', '__path__', '__all__', 'after', 'one'} <= set(dir(star_pkg))
    assert len(dir(star_pkg)) == len(set(dir(star_pkg)))  # loaded names are listed once


def test_duplicate_name(make_pkg):
    # 2.15: two modules exporting the same name is an error naming both files, not a silent pick.
    make_pkg('dup_pkg', {'a.py': 'same = "a"\n', 'sub/b.py': 'same = "b"\n'})
    error = re.escape("`importer()` found name 'same' in both '") + '.*a.py' + re.escape("' and '") + '.*b.py'
    with pytest.raises(ImportError, match=error):
        import dup_pkg  # noqa


def test_private_names(make_pkg):
    # 2.16: without `__all__` names starting with `_` are not exported, like `from mod import *`.
    make_pkg('priv_pkg', {'a.py': '_hidden = 1\nshown = 2\n', 'b.py': '__all__ = ["_listed"]\n_listed = 3\n'})
    import priv_pkg
    assert priv_pkg.shown == 2
    assert priv_pkg._listed == 3  # `__all__` decides
    with pytest.raises(ImportError):
        from priv_pkg import _hidden  # noqa
    assert '_hidden' not in dir(priv_pkg)


@pytest.mark.parametrize('first', ['import', 'lazy'])
def test_name_like_sub_module(make_pkg, first):
    # 2.17: `pkg.one` is the exported `one()`, whether `import pkg.one` or `from pkg import one` comes first.
    name = f'same_{first}_pkg'
    make_pkg(name, {'one.py': 'def one():\n    return 1\n'})
    pkg = importlib.import_module(name)
    if first == 'import':
        importlib.import_module(f'{name}.one')  # like `import pkg.one`
    one = pkg.one
    assert one() == 1
    importlib.import_module(f'{name}.one')
    assert pkg.one is one
    assert type(sys.modules[f'{name}.one']).__name__ == 'module'
    assert sys.modules[f'{name}.one'].one is one


def test_missing_attribute(make_pkg):
    # 10.1: same error as a normal module, without a trailing newline.
    make_pkg('attr_pkg', {'mod.py': 'one = 1\n'})
    import attr_pkg
    with pytest.raises(AttributeError) as error:
        attr_pkg.two
    assert str(error.value) == "module 'attr_pkg' has no attribute 'two'"
    assert (error.value.name, error.value.obj) == ('two', attr_pkg)


def test_import_light():
    # 9.1: modules only a scan needs are not loaded by `import dynamic_import`, which runs on every cache hit.
    code = 'import sys\nbefore = set(sys.modules)\nimport dynamic_import\nprint(*set(sys.modules) - before)\n'
    env = os.environ | {'PYTHONPATH': os.pathsep.join(sys.path)}
    loaded = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True, text=True, check=True)
    assert not {'ast', 'glob', 'mmap', 're'} & set(loaded.stdout.split())


def test_processes_uncached(make_pkg):
    # 2.18: processes starting together on an uncached package all import fine and leave one valid cache.
    files = {f'mod{i}.py': f'name{i} = {i}\n' for i in range(200)}
    pkg = make_pkg('proc_pkg', files)
    code = 'import proc_pkg\nassert proc_pkg.name199 == 199\n'
    env = os.environ | {'PYTHONPATH': os.pathsep.join(sys.path)}
    procs = [subprocess.Popen([sys.executable, '-c', code], env=env) for _ in range(8)]
    assert [p.wait() for p in procs] == [0] * 8
    assert os.path.exists(pkg_cache_path(os.path.join(pkg, ''), '__init__.py', 'importer'))
    assert not [i for i in os.listdir(pkg / '__pycache__') if i.endswith('.tmp')]
    assert subprocess.run([sys.executable, '-c', code], env=env).returncode == 0  # reads that cache


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


def test_pycache_prefix(tmp_path, make_pkg, monkeypatch):
    # 1.2: with `sys.pycache_prefix` every package gets its own cache file under the prefix.
    prefix = tmp_path / 'prefix' / 'deeper'  # parent does not exist yet
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
