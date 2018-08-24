Dynamic Import
==============

Lets you dynamically/lazily import python module on run-time, enables easy to use import path name, saves memory. Also makes managing projects easy by not having to worry about nested folder structure producing long import names.


Install
-------

use `pip`_ to install:

.. code-block:: text

    pip install dynamic-import


Example
-------

./example/sample/__init__.py

.. code-block:: python
    
    from dynamic_import import importer

    # Static Importer
    from .static import static
    # Note
    #   This is to demonstrate that you can still import modules directly
    #   before "importer()" is called.

    # Dynamic Importer
    importer(
        __package__,
        {
            '.one': ('a', 'b', 'c'),  # from .one import a, b, c
            '.two': ('x', 'y', 'z'),  # from .two import x, y, z
            '.local': 'internals',    # from .local import internals
            # Note -------^
            #   Here we are using str vs Iterable[str] type since its only
            #   1 value. This will also work.
        }
    )



./example/example.py

.. code-block:: python

    # Static Import #1
    # ----------------
    from sample import static
    print(static())
    print()
    # Note
    #   Only "sample" & "sample.static" modules are loaded at this point.

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

    # Dynamic Import #3
    # -----------------
    from sample import internals
    print(internals())
    # Note
    #   This is to demonstrate you can relatively import one module from another module.


License
-------
Free, No limit what so ever. `Read more`_


TODO
----
    - Add multi-dimensional dictionary to module naming convention.

.. _pip: https://pip.pypa.io/en/stable/quickstart/
.. _Read more: https://github.com/YoSTEALTH/Dynamic-Import/blob/master/LICENSE.txt
