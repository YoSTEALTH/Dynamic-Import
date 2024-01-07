|test-status|

Dynamic Import 
==============

Let Dynamic Import handle your projects(package) import needs. Enables you to dynamically(lazily) import module as needed on run-time.

* Place ``importer()`` into top ``__init__.py`` file and forget about where variable, function, class, ... is located!
* Move/rename file within your project? No problem, auto updates. 
* Just call ``from <package> import <variable>`` while coding and when end-user calls from your project. All names are accessible at top level, easy to remember.
* Supports ``.py`` and ``.so`` (experimental)
* Saves memory.

Ultimate worry free management comfort as your project grows from small to large.


Requires
--------

    - Python 3.8+


Install, update & uninstall
---------------------------

Use `pip`_ to:

.. code-block:: bash

    python3 -m pip install --user dynamic-import            # install

    python3 -m pip install --user --upgrade dynamic-import  # update

    python3 -m pip uninstall dynamic-import                 # uninstall


Example
-------

./example/pkg/__init__.py

.. code-block:: python

    from dynamic_import import importer


    importer()  # only need to call `importer()` once in main `__init__.py` file.

    # note: `importer()` will scan all package directory and sub-directories for `.py, .so`
    # files and cache import names for later use.


./example/pkg/var.py

.. code-block:: python

    import sys

    # just like normal import if `__all__` is not defined, `my_var` will be included.
    # Also `sys` will not be included.

    my_var = sys.version_info.major


./example/pkg/functions/myfunction.py

.. code-block:: python

    # all import names are available at higher level, 
    # no need for `from ..example.var import my_var`
    from pkg import my_var


    __all__ = 'my_function'  # using just string for single name is ok


    def my_function():
        return my_var + 1


./example/classes/__init__.py

.. code-block:: python

    __all__ = ['MyClass']


    class MyClass:
        pass


./example/calling.py

.. code-block:: python

    # you can import all 3 names regardless of where they are located as:
    from pkg import my_var, my_function, MyClass
    # or 
    import pkg

    print(my_var, pkg.my_var == my_var)
    print(my_function())
    MyClass()
    print(dir(pkg))


.. code-block:: python

    # see all importable names by:
    >>> import pkg
    >>> dir(pkg)  # this will only show names without actually loading modules.
    ['my_var', 'my_function', 'MyClass', ...]


Other ``importer()`` Usage
------------------------
./__init__.py

.. code-block:: python

    from dynamic_import import importer

    # disable & remove cache file
    importer(cache=False)

    # do not scan sub-directories
    importer(recursive=False)

    # exclude sub-directories
    importer(exclude_dir='sub-directory-one')  # `exclude_dir: str`
    importer(exclude_dir=('sub-directory-one', 'sub-directory-two'))  # `exclude_dir: Tuple[str]`


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
    - Special name that start and end with ``"__"`` are not allowed, e.g: ``__something__``
    - Using ``from <package> import *`` is not recommended unless you want to load all the modules.
    - No need to have empty ``__init__.py`` inside sub-directories. Namespace + Package combined into one.


Experimental
------------
    - ``importer()`` also works with certain ``.so`` file (tested with cython created ``.so``).
    - ``.so`` should not contain any function/class that auto-run on import, e.g: ``run_something()``


License
-------
Free, Public Domain (CC0). `Read more`_

.. _pip: https://pip.pypa.io/en/stable/quickstart/
.. _Read more: https://github.com/YoSTEALTH/Dynamic-Import/blob/master/LICENSE.txt
.. |test-status| image:: https://github.com/yostealth/dynamic-import/actions/workflows/test.yml/badge.svg?branch=master&event=push
    :target: https://github.com/yostealth/dynamic-import/actions/workflows/test.yml
    :alt: Test status
