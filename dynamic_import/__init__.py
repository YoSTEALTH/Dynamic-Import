from .importer import importer
from .version import version


__all__ = 'importer',
__version__ = version
# Q) Hey!!! Why does Dynamic Import not use `importer()` to manage this project???
# A) Would have been really nice, though its a circular import nightmare. Tail-chasing.
