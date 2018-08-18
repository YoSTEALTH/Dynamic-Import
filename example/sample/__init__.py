try:
    # Installed version
    from dynamic_import import importer
except ImportError:
    # Local version
    import sys
    import os.path
    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    )
    from dynamic_import import importer


# Static Importer
from .direct import static  # noqa
# Note
#   This is to demonstrate that you can still import modules directly
#   before "importer()" is called.

# Dynamic Importer
importer(
    __package__,
    {
        '.one': ('a', 'b', 'c'),  # from .one import a, b, c
        '.two': ('x', 'y', 'z'),  # from .two import x, y, z
        '.local': ('o',),
    }
)
