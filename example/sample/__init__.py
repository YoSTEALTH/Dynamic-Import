try:
    from dynamic_import import importer
except ImportError:
    # Development testing module location
    import sys
    import os.path
    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    )
    from dynamic_import import importer


# Static/Normal Import
from .static import static  # noqa
# Note
#   This is to demonstrate that you can still import modules directly
#   before "importer()" is called.

# Dynamic Importer
importer(
    {
        'one': ('a', 'b', 'c'),  # from .one import a, b, c
        'two': ('x', 'y', 'z'),  # from .two import x, y, z
        'local': 'internals',    # from .local import internals
        'sub': {
            'page': ('e', 'f', 'g'),  # from .sub.page import e, f, g
            'name': 'name',           # from .sub.name import name
            # |--------^ Here we are using str vs Iterable[str] type since its
            # only 1 value. This will also work.
        }
    }
)

# Note
#   - you can still use static/normal import e.g: "from .module import example"
#     before "importer()" is called.
#   - You can also use "." e.g: '.one': ('a', 'b', 'c')
#   - for 1 word import name you can use 'name': 'name' vs 'name': ('name',)
#   - All import names must be unique.
