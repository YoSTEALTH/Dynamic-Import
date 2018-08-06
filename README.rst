Smuggler
========

Smuggler is dynamic python run-time importer and easy to use module
import path name.

Install
-------

Install directly from pip using:

.. code-block:: text

    pip install smuggler


Example
-------

./example/sample/__init__.py

.. code-block:: python
    
    from smuggler import importer

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
    #   Only "sample", "sample.direct" & "sample.one" modules are loaded at this point.

    # Dynamic Import #2
    # -----------------
    from sample import x, y, z
    print(x())
    print(y())
    print(z())
    # Note
    #   All "sample", "sample.direct", "sample.one" & "sample.two" modules are loaded.
