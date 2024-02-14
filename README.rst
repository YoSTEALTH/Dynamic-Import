|test-status| |downloads|

Dynamic Import
==============

Let Dynamic Import handle your projects(package) import needs. Enables you to dynamically(lazily) import module as needed within the project and for external usage on run-time.

* Place ``importer()`` into top ``__init__.py`` file and forget about where variable, function, class, ... are located.
* Just call ``from <package> import <variable>`` while coding and when end-user calls from your project. All names are accessible at top level, easy to remember.
* Move/rename file within your project? No problem, auto updates. 
* Supports ``.py`` and ``.so`` (experimental)
* Saves memory.

Ultimate worry free management comfort as your project grows from small to large.


Requires
--------

    - Python 3.8+
    - Linux, MacOS


Install, update & uninstall
---------------------------

Use `pip`_ to:

.. code-block:: bash

    python3 -m pip install dynamic-import            # install

    python3 -m pip install --upgrade dynamic-import  # update

    python3 -m pip uninstall dynamic-import          # uninstall


Install directly from GitHub
____________________________


.. code-block:: bash

    python3 -m pip install --upgrade git+https://github.com/YoSTEALTH/Dynamic-Import


Usage
-----

.. code-block:: python

    # ./<package>/__init__.py
    from dynamic_import import importer

    importer()


``importer()`` options
______________________


.. code-block:: python

    importer(cache=False)  # disable & remove cache file (for temporary use only!)

    importer(recursive=False)  # do not scan sub-directories

    # exclude `.py, .so` file
    importer(exclude_file='file.py')                          # single
    importer(exclude_file=('one.py', 'sub-dir/two.py', ...))  # multiple

    # exclude sub-directory
    importer(exclude_dir='sub-dir')                        # single
    importer(exclude_dir=('sub-dir', 'sub/sub-dir', ...))  # multiple


Example
-------

.. code-block:: python

    # ./example/pkg/__init__.py
    from dynamic_import import importer


    __version__ = '1.2.3'  # if need to use special name place it above `importer()`

    importer()  # only need to call `importer()` once inside main `__init__.py` file.

    # note: `importer()` will scan all package directory and sub-directories for `.py, .so`
    # files and cache import names for dynamic use.


.. code-block:: python

    # ./example/pkg/var.py
    import sys

    # just like normal import if `__all__` is not defined, `my_var` will be included.
    # Also `sys` will not be included.

    my_var = sys.version_info.major


.. code-block:: python

    # ./example/pkg/functions/myfunction.py
    from pkg import my_var
    # all import names are available at higher level, 
    # no need for `from ..example.var import my_var`

    __all__ = 'my_function'  # using just string for single name is ok


    def my_function():
        return my_var + 1


.. code-block:: python

    # ./example/classes/__init__.py

    __all__ = ['MyClass']


    class MyClass:
        pass


Calling
_______


.. code-block:: python

    # ./example/calling.py
    from pkg import my_var, my_function, MyClass  # import all 3 names regardless of where module is located

    # or 
    import pkg

    MyClass()
    print(my_var, pkg.my_var is my_var) # 3 True
    print(my_function())                # 4
    print(dir(pkg))                     # ['my_var', 'my_function', 'MyClass', ...]


Note
----
    - Only need to call ``importer()`` once inside ``__init__.py`` file.
    - All sub-directories will be scanned for ``.py, .so`` file as ``recursive=True`` by default.
    - Use ``exclude_dir`` to list sub-directories you would like to avoid scanning.
    - You can still use normal static/relative import.
    - For one word import name you can use string e.g. ``__all__ = 'function'`` vs ``__all__ = ('function',)``
    - All import names must be unique.
    - Cache can be disabled & removed by using ``importer(cache=False)``
    - Cached temporary files are stored in ``./__pycache__/__init__.importer-<python-version>.pyc``
    - You can move or rename any ``.py`` file within project directory or sub-directory and import will not break.
    - Special name e.g: ``__something__`` are ignored. If need to use special name place it 
      above ``importer()`` e.g: ``__version__ = '1.2.3'; importer()``
    - Using ``from <package> import *`` is not recommended unless you want to load all the modules.
    - No need to have empty ``__init__.py`` inside sub-directories. Namespace + Package combined into one.
    - Calling ``dir(<package>)`` enables you to show all importable names without actually loading modules.
    - Having module name and function name the same is ok! e.g. ``from pkg import my_fun`` while ``./pkg/my_fun.py``
      and calling `my_fun()` will not conflict with module name. Module will still load in the background.


Experimental
------------
    - ``importer()`` also works with certain ``.cpython-<...>.so`` ``.abi3.so`` file (tested with cython created ``.so``).
    - ``.so`` should not contain any function/class that auto-run on import, e.g: ``run_something()``
    - Visit `Liburing`_ to see project using Dynamic Import with ``.so`` files in action.


License
-------
Free, Public Domain (CC0). `Read more`_

.. _pip: https://pip.pypa.io/en/stable/getting-started/
.. _Read more: https://github.com/YoSTEALTH/Dynamic-Import/blob/master/LICENSE.txt
.. _Liburing: https://github.com/YoSTEALTH/Liburing
.. |test-status| image:: https://github.com/yostealth/dynamic-import/actions/workflows/test.yml/badge.svg?branch=master&event=push
    :target: https://github.com/yostealth/dynamic-import/actions/workflows/test.yml
    :alt: Test status
.. |downloads| image:: https://img.shields.io/pypi/dm/dynamic_import
   :alt: PyPI - Downloads
