import os
import re
import sys
import json
import shlex
import shutil
import sysconfig
import subprocess
import pytest
import dynamic_import
from importlib import import_module
from importlib.util import find_spec
from importlib.machinery import EXTENSION_SUFFIXES
from dynamic_import.extract import extract_so_variable


SUFFIX = EXTENSION_SUFFIXES[0]  # e.g: '.cpython-315-x86_64-linux-gnu.so', Windows: '.cp315-win_amd64.pyd'
# real extension modules shipped by CPython, one public name each that exists on every supported version.
if sys.platform == 'win32':  # `_bisect` & co. are built into `python3XY.dll`; these are own `.pyd` files in `DLLs\`
    SO_NAME = {'unicodedata': 'lookup', '_queue': 'SimpleQueue', 'winsound': 'Beep'}  # no dependent `.dll`
else:
    SO_NAME = {'_bisect': 'bisect_left', '_heapq': 'heappush', '_json': 'scanstring'}
SO_FIRST, SO_FIRST_NAME = next(iter(SO_NAME.items()))  # e.g: '_bisect', 'bisect_left'


def so_files(*names):
    ''' Read real extension modules shipped with the interpreter (no compiler or Cython needed).

        Type
            names:  tuple[str]
            return: dict[str, bytes]   e.g: {'_bisect.cpython-315-x86_64-linux-gnu.so': b'...'}

        Note
            - files keep their own name: the init symbol (`PyInit__bisect`) must match the module base name.
            - Windows ships them untagged (`DLLs\\unicodedata.pyd`); the copy gets `SUFFIX`, the loader only
              checks the file name.
            - skips the test if the interpreter has the module built in (static build, no `.so` file).
    '''
    files = {}
    for name in names:
        path = find_spec(name).origin  # 'built-in' for a static build, also right inside a venv
        if not path.endswith(tuple(EXTENSION_SUFFIXES)):
            pytest.skip(f'{name!r} is not a separate extension module file on this interpreter')
        with open(path, 'rb') as f:
            files[name + SUFFIX] = f.read()
    return files


def test_so_scan_and_load(make_pkg):
    # 6.8: names of every `.so` are found, a name loads its `.so`, plain `libfoo.so` / `foo.dll` are ignored.
    lib = {'libfoo.so': b'not an extension', 'foo.dll': b'not an extension'}
    make_pkg('so_scan_pkg', so_files(*SO_NAME) | lib | {'mod.py': 'plain = 1\n'})
    import so_scan_pkg
    names = dir(so_scan_pkg)
    for name in (*SO_NAME.values(), 'plain'):
        assert name in names
    for name in ('libfoo', 'foo'):
        assert name not in names and f'so_scan_pkg.{name}' not in sys.modules

    from so_scan_pkg import plain
    assert plain == 1
    for module, name in SO_NAME.items():
        value = getattr(so_scan_pkg, name)
        assert value.__name__ == name
        assert value is getattr(sys.modules[f'so_scan_pkg.{module}'], name)
        assert sys.modules[f'so_scan_pkg.{module}'].__file__.endswith(SUFFIX)
    if sys.platform != 'win32':
        assert so_scan_pkg.bisect_left([1, 2, 3], 2) == 1
    else:
        assert so_scan_pkg.lookup('LATIN SMALL LETTER A') == 'a'


def test_so_exclude_file(make_pkg):
    (keep, keep_name), (skip, skip_name) = list(SO_NAME.items())[:2]  # e.g: ('_bisect', ...), ('_heapq', ...)
    init = f'from dynamic_import import importer\nimporter(exclude_file="{skip}{SUFFIX}")\n'
    make_pkg('so_exclude_pkg', so_files(keep, skip) | {'__init__.py': init})
    import so_exclude_pkg
    assert keep_name in dir(so_exclude_pkg)
    assert skip_name not in dir(so_exclude_pkg)
    assert f'so_exclude_pkg.{skip}' not in sys.modules  # not even imported during the scan


SCRIPT = f'''
import sys, json
def loaded():
    return sorted(n for n in sys.modules if n.startswith('so_lazy_pkg.'))
import so_lazy_pkg
before = loaded()
so_lazy_pkg.{SO_FIRST_NAME}
print(json.dumps([before, loaded()]))
'''


def test_so_lazy_with_cache(make_pkg):
    # 6.8: run 1 (no cache) imports every `.so` during the scan to learn its names (see 6.9);
    #      run 2 (cache) imports none until a name is used, then only that one.
    pkg = make_pkg('so_lazy_pkg', so_files(*SO_NAME))
    path = os.pathsep.join((os.path.dirname(os.path.dirname(dynamic_import.__file__)), str(pkg.parent)))
    env = os.environ | {'PYTHONPATH': path}

    def run():
        out = subprocess.run([sys.executable, '-c', SCRIPT], env=env, capture_output=True, text=True, check=True)
        return json.loads(out.stdout)

    all_so = sorted(f'so_lazy_pkg.{name}' for name in SO_NAME)
    assert run() == [all_so, all_so]
    assert run() == [[], [f'so_lazy_pkg.{SO_FIRST}']]


C_MODULE = '''
#include <Python.h>

static PyObject *hello(PyObject *self, PyObject *name) {
    return PyUnicode_FromFormat("Hello %%S!", name);
}

static PyMethodDef methods[] = {{"hello_%(name)s", hello, METH_O, NULL}, {NULL, NULL, 0, NULL}};

static int exec_module(PyObject *module) {
    PyObject *all = %(all)s;  /* value of `__all__`, NULL: not defined */
    if (all == NULL) {
        return PyErr_Occurred() ? -1 : 0;
    }
    int r = PyModule_AddObjectRef(module, "__all__", all);
    Py_DECREF(all);
    return r;
}

static PyModuleDef_Slot slots[] = {
    {Py_mod_exec, exec_module},
#ifdef Py_mod_gil
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},  /* free-threaded build: do not re-enable the GIL */
#endif
    {0, NULL}
};

static struct PyModuleDef def = {PyModuleDef_HEAD_INIT, "%(name)s", NULL, 0, methods, slots};

PyMODINIT_FUNC PyInit_%(name)s(void) {
    return PyModuleDef_Init(&def);
}
'''


def build_so(directory, name, all_value='NULL', suffix=SUFFIX, source=None):
    ''' Compile a tiny C extension module with the interpreter's own build settings (no Cython, no setuptools).

        Type
            directory: pathlib.Path
            name:      str
            all_value: str            C expression for `__all__`, e.g: 'Py_BuildValue("[s]", "hello_x")'
            suffix:    str            one of `EXTENSION_SUFFIXES`, e.g: '.abi3.so'
            source:    str | None     C source to build instead of the module, e.g. a plain shared library
            return:    pathlib.Path   e.g: '<directory>/<name>.cpython-315-x86_64-linux-gnu.so'

        Note
            - the module defines `hello_<name>(name)` returning `'Hello <name>!'`.
            - skips the test if there is no C compiler or no `Python.h`.
            - always built against the full API: the loader picks a file by its suffix and never checks the ABI,
              and a limited API (`abi3`/`abi3t`) build is not possible on every interpreter (e.g. 3.14t).
    '''
    include = sysconfig.get_path('include')
    ldshared = shlex.split(sysconfig.get_config_var('LDSHARED') or '')
    if not ldshared or not shutil.which(ldshared[0]) or not os.path.isfile(os.path.join(include, 'Python.h')):
        pytest.skip('no C compiler or Python headers to build an extension module')
    directory.mkdir(parents=True, exist_ok=True)
    src = directory / f'{name}.c'
    src.write_text(C_MODULE % {'name': name, 'all': all_value} if source is None else source)
    out = directory / (name + suffix)
    ccshared = shlex.split(sysconfig.get_config_var('CCSHARED') or '')  # e.g: '-fPIC'
    cmd = [*ldshared, *ccshared, f'-I{include}', str(src), '-o', str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    src.unlink()  # only the `.so` belongs in the package
    return out


def test_so_built_all_forms(make_pkg):
    # replaces the Cython test: `.so` without `__all__`, with a list and with a string `__all__`.
    pkg = make_pkg('so_built_pkg', {})
    build_so(pkg, 'one')
    build_so(pkg, 'two', 'Py_BuildValue("[s]", "hello_two")')
    build_so(pkg, 'three', 'PyUnicode_FromString("hello_three")')
    import so_built_pkg
    assert {'hello_one', 'hello_two', 'hello_three'} <= set(dir(so_built_pkg))

    from so_built_pkg import hello_one, hello_two, hello_three
    assert hello_one('World') == 'Hello World!'
    assert hello_two('World') == 'Hello World!'
    assert hello_three('World') == 'Hello World!'
    assert hello_two is sys.modules['so_built_pkg.two'].hello_two


def test_so_built_extract(tmp_dir, monkeypatch):
    build_so(tmp_dir, 'so_extract_one')
    build_so(tmp_dir, 'so_extract_two', 'Py_BuildValue("(ss)", "hello_so_extract_two", "extra")')
    build_so(tmp_dir, 'so_extract_error', 'PyLong_FromLong(123)')
    monkeypatch.syspath_prepend(str(tmp_dir))
    assert extract_so_variable('so_extract_one') == ['hello_so_extract_one']
    assert extract_so_variable('so_extract_two') == ['hello_so_extract_two', 'extra']
    with pytest.raises(TypeError, match=re.escape("can not parse `__all__` value in 'so_extract_error'")):
        extract_so_variable('so_extract_error')


@pytest.mark.parametrize('suffix', EXTENSION_SUFFIXES)
def test_so_every_suffix(make_pkg, suffix):
    # every name `importlib.machinery.EXTENSION_SUFFIXES` lists on this interpreter, e.g. on 3.15:
    # '.cpython-315-x86_64-linux-gnu.so', '.abi3-x86_64-linux-gnu.so', '.abi3.so', '.abi3t-...so', '.abi3t.so', '.so'
    name = f'so_suffix_pkg_{EXTENSION_SUFFIXES.index(suffix)}'
    init = f'from dynamic_import import importer\nimporter(exclude_file="skip{suffix}")\n'
    pkg = make_pkg(name, {'__init__.py': init})
    build_so(pkg, 'ext', suffix=suffix)
    build_so(pkg, 'skip', suffix=suffix)
    module = import_module(name)
    assert module.hello_ext('World') == 'Hello World!'
    assert sys.modules[f'{name}.ext'].__file__.endswith(suffix)
    assert 'hello_skip' not in dir(module)  # `exclude_file` accepts this suffix
    assert f'{name}.skip' not in sys.modules


C_LIBRARY = '''
int add(int a, int b) {
    return a + b;
}
'''


def test_so_bare_module_and_library(make_pkg):
    # an untagged `.so` is scanned only if it is an extension module (`liburing.so`), a plain shared library
    # bundled with the package (`libfoo.so`) is skipped without being loaded.
    if '.so' not in EXTENSION_SUFFIXES:
        pytest.skip('this platform has no bare `.so` extension suffix')
    pkg = make_pkg('so_bare_pkg', {'libempty.so': b'', 'libjunk.so': b'not an extension'})
    build_so(pkg, 'libring', suffix='.so')
    build_so(pkg, 'libfoo', suffix='.so', source=C_LIBRARY)
    import so_bare_pkg
    assert 'hello_libring' in dir(so_bare_pkg)
    for lib in ('libfoo', 'libempty', 'libjunk'):
        assert f'so_bare_pkg.{lib}' not in sys.modules
    assert so_bare_pkg.hello_libring('World') == 'Hello World!'
    assert sys.modules['so_bare_pkg.libring'].__file__.endswith(os.sep + 'libring.so')
