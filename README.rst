Dynamic Import
==============

Lets you dynamically/lazily import python module on run-time. Also enables easy to use import path name.


Install
-------

use `pip`_ to install:

.. code-block:: text

    pip install dynamic_import


Example
-------

./example/sample/__init__.py

.. code-block:: python
    
    from dynamic_import import importer


    # Static Importer
    from .direct import static
    # Note
    #   This is to demonstrate that you can still import modules directly
    #   before "importer()" is called.

    # Dynamic Importer
    importer(
        __package__,
        {
            '.one': ('a', 'b', 'c'),  # same as ```from .one import a, b, c```
            '.two': ('x', 'y', 'z'),  # same as ```from .two import x, y, z```
        }
    )


./example/example_1.py

.. code-block:: python

    # Static Import #1
    # ----------------
    from sample import static
    print(static())
    print()
    # Note
    #   Only "sample" & "sample.direct" modules are loaded at this point.

    # Dynamic Import #1
    # -----------------
    from sample import a, b, c
    print(a())
    print(b())
    print(c())
    print()
    # Note
    #   Now "sample", "sample.direct" & "sample.one" modules are loaded at this point.

    # Dynamic Import #2
    # -----------------
    from sample import x, y, z
    print(x())
    print(y())
    print(z())
    # Note
    #   All "sample", "sample.direct", "sample.one" & "sample.two" modules are loaded.


.. _pip: https://pip.pypa.io/en/stable/quickstart/
