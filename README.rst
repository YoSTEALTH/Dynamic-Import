Dynamic Import
==============

Lets you dynamically/lazily import python module on run-time, enables easy to use import path name, saves memory. Also makes managing projects easy by not having to worry about nested folder structure producing long import names.


Warning
-------
```importer()``` argument was changed in version "0.9.4". No need to manually provide ```__package__``` name. Will raise DeprecationWarning in future releases.


Install, update & uninstall
---------------------------

Use `pip`_ to:

.. code-block:: text

    pip install dynamic-import

    pip install --upgrade dynamic-import

    pip uninstall dynamic-import


Example
-------

./example/sample/__init__.py

.. code-block:: python
    
    from dynamic_import import importer

    # Static/Normal Import
    from .static import static

    # Dynamic Importer
    importer(
        {
            'one': ('a', 'b', 'c'),  # from .one import a, b, c
            'two': ('x', 'y', 'z'),  # from .two import x, y, z
            'local': 'internals',    # from .local import internals
            'sub': {
                'page': ('e', 'f', 'g'),  # from .sub.page import e, f, g
                'name': 'name',           # from .sub.name import name
            }
        }
    )

./example/example.py

.. code-block:: python

    # Static Import #1
    # ----------------
    from sample import static
    # Only "sample" & "sample.static" modules are loaded at this point.
    print(static())
    print()

    # Dynamic Import #1
    # -----------------
    from sample import a, b, c
    # Now "sample", "sample.static" & "sample.one" modules are loaded at this point.
    print(a())
    print(b())
    print(c())
    print()

    # Dynamic Import #2
    # -----------------
    from sample import x, y, z
    # All "sample", "sample.static", "sample.one" & "sample.two" modules are loaded.
    print(x())
    print(y())
    print(z())
    print()

    # Dynamic Import #3
    # -----------------
    from sample import internals
    # This is to demonstrate you can relatively import one module from another module.
    print(internals())
    print()

    # Sub-page Import #1
    # ------------------
    from sample import e, f, g
    # This demonstrates you can use nested sub-dir and use main module to import from.
    print(e())
    print(f())
    print(g())
    print()

    # Sub-page Import #2
    # ------------------
    from sample import name
    # Another sub-dir example
    print(name())
    print()


Note
----
    - you can still use static/normal import e.g. ```from .module import example``` before `importer()` is called.
    - You can also use `.` e.g. ```'.one': ('a', 'b', 'c')```
    - for 1 word import name you can use ```'module': 'myclass'``` vs ```'module': ('myclass',)```
    - All import names must be unique.


License
-------
Free, No limit what so ever. `Read more`_


.. TODO
.. ----
    - Add multi-dimensional dictionary to module naming convention. Done, local testing.
    - Remove "__package__" attribute from importer(), should be automatic!. Done, local testing.

.. _pip: https://pip.pypa.io/en/stable/quickstart/
.. _Read more: https://github.com/YoSTEALTH/Dynamic-Import/blob/master/LICENSE.txt
