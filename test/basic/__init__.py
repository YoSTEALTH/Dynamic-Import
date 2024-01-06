try:
    from dynamic_import import importer
except ImportError:
    # Development testing module location
    import sys
    import os.path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
    from dynamic_import import importer


importer()

__all__ = 'DEFINE', 're_import'
DEFINE = 123


def re_import():
    pass
