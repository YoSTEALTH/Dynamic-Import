[![Test status](https://github.com/yostealth/dynamic-import/actions/workflows/test.yml/badge.svg?branch=master&event=push)](https://github.com/yostealth/dynamic-import/actions/workflows/test.yml)
![PyPI - Downloads](https://img.shields.io/pypi/dm/dynamic_import)

# Dynamic Import

Let Dynamic Import handle your projects(package) import needs. Enables you to dynamically(lazily)
import module as needed within the project and for external usage on run-time.

* Place `importer()` into top `__init__.py` file and forget about where
  variable, function, class, ... are located.
* Just call `from <package> import <variable>` while coding and when end-user calls from your
  project. All names are accessible at top level, easy to remember.
* Move/rename file within your project? No problem, auto updates.
* Supports `.py` and extension module `.so` (`.pyd` on Windows) files (experimental)
* Saves memory(for medium to large projects).

Ultimate worry free management comfort as your project grows from small to large.


## Requires

- Python 3.11+
- Linux, MacOS, Windows


## Install, update & uninstall

Use [pip](https://pip.pypa.io/en/stable/getting-started/) to:

```bash
python3 -m pip install dynamic-import            # install

python3 -m pip install --upgrade dynamic-import  # update

python3 -m pip uninstall dynamic-import          # uninstall
```


### Install directly from GitHub

```bash
python3 -m pip install --upgrade git+https://github.com/YoSTEALTH/Dynamic-Import
```


## Usage

```python
# ./<package>/__init__.py
from dynamic_import import importer

importer()
```


### `importer()` options

```python
importer(cache=False)  # disable & remove cache file (for temporary use only!)

importer(recursive=False)  # do not scan sub-directories

# exclude `.py, .so` file
importer(exclude_file='file.py')                          # single
importer(exclude_file=('one.py', 'sub-dir/two.py', ...))  # multiple

# exclude sub-directory
importer(exclude_dir='sub-dir')                        # single
importer(exclude_dir=('sub-dir', 'sub/sub-dir', ...))  # multiple
```


## Example

```python
# ./example/pkg/__init__.py
from dynamic_import import importer


__version__ = '1.2.3'  # if need to use special name place it above `importer()`

importer()  # only need to call `importer()` once inside main `__init__.py` file.

# note: `importer()` will scan all package directory and sub-directories for `.py, .so`
# files and cache import names for dynamic use.
```

```python
# ./example/pkg/var.py
import sys

# just like normal import if `__all__` is not defined, `my_var` will be included.
# Also `sys` will not be included.

my_var = sys.version_info.major
```

```python
# ./example/pkg/functions/myfunction.py
from pkg import my_var
# all import names are available at higher level,
# no need for `from ..example.var import my_var`

__all__ = 'my_function'  # using just string for single name is ok


def my_function():
    return my_var + 1
```

```python
# ./example/pkg/classes/__init__.py

__all__ = ['MyClass']


class MyClass:
    pass
```


### Calling

```python
# ./example/calling.py
# import all 3 names regardless of where module is located
from pkg import my_var, my_function, MyClass

# or
import pkg

MyClass()
print(my_var, pkg.my_var is my_var) # 3 True
print(my_function())                # 4
print(dir(pkg))                     # ['my_var', 'my_function', 'MyClass', ...]
```


## Note

- Only need to call `importer()` once inside `__init__.py` file.
- All sub-directories will be scanned for `.py, .so` file as `recursive=True` by default.
- Use `exclude_dir` to list sub-directories you would like to avoid scanning.
- You can still use normal static/relative import.
- For one word import name you can use string
  e.g. `__all__ = 'function'` vs `__all__ = ('function',)`
- All import names must be unique.
- Cache can be disabled & removed by using `importer(cache=False)`
- Cached temporary files are stored in `./__pycache__/__init__.importer-<python-version>.pyc`
  (or under `sys.pycache_prefix` when set). If the cache can not be written (read-only install)
  `importer()` runs without cache.
- `__all__` must be a literal list, tuple or string; `__all__ += [...]` is fine. Without `__all__`
  only top-level assignments, `def` and `class` are found; names defined inside `if`/`try`
  blocks are not.
- A lazily loaded module is registered in `sys.modules` so `import pkg.sub.module` reuses it.
- A parent `importer(recursive=False)` lets sub-packages call `importer()` themselves.
- You can move or rename any `.py` file within project directory or sub-directory and
  import will not break.
- Special name e.g: `__something__` are ignored. If need to use special name place it
  above `importer()` e.g. `__version__ = '1.2.3'; importer()`
- Using `from <package> import *` is not recommended unless you want to load all the modules.
- No need to have empty `__init__.py` inside sub-directories. Its "like" Namespace + Package
  combined into one! but not technically.
- Calling `dir(<package>)` enables you to show all importable names without loading modules.


## Experimental

- Having module name and function name the same is ok! e.g. `from pkg import my_fun` while
  `./pkg/my_fun.py` and calling `my_fun()` will not conflict with module name. Module will
  still load in the background.
- `importer()` also works with every extension module suffix Python supports
  (`importlib.machinery.EXTENSION_SUFFIXES`): `.cpython-<...>.so`, `.abi3<...>.so`, plain `.so` on Linux/macOS,
  `.cp<...>.pyd` & `.pyd` on Windows. A plain `.so` without a Python init function (a bundled `libfoo.so`
  shared library) is ignored, without being loaded.
- `.so` should not contain any function/class that auto-run on import e.g. `run_something()`
- To find the names inside a `.so` file it has to be imported, so the first run (no cache yet) imports
  every `.so` once. Later runs use the cache and load each `.so` only when one of its names is used.
  If the cache can not be written (e.g. read-only install) every run behaves like the first one.
- Visit [Liburing](https://github.com/YoSTEALTH/Liburing) to see project using Dynamic Import with `.so` files
  in action.


## License

Free, Public Domain (CC0). [Read more](https://github.com/YoSTEALTH/Dynamic-Import/blob/master/LICENSE.txt)
