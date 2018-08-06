try:
    # Installed version
    from noname import dynamic_importer
except ImportError:
    # Local version
    import sys
    import os.path
    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    )
    from noname import dynamic_importer


# Static Importer
from .direct import static  # noqa
# Note
#   This is to demonstrate that you can still import modules directly
#   before "dynamic_importer()" is called.

# Dynamic Importer
dynamic_importer(
    __package__,
    {
        '.one': ('a', 'b', 'c'),  # from .one import a, b, c
        '.two': ('x', 'y', 'z'),  # from .two import x, y, z
    }
)
