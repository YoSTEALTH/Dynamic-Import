try:
    from dynamic_import import importer
except ModuleNotFoundError:
    import sys
    import os.path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from dynamic_import import importer


importer()  # only need to call `importer()` once in main `__init__.py` file.
# note: `importer()` will scan all package directory and sub-directories for `.py, .so`
# files and cache import names for later use.
