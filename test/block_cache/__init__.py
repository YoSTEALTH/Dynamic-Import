from dynamic_import import importer


__block1__ = 11  # this should be allowed to be imported and accessible.

importer(cache=True)

__block2__ = 22  # this should not be allowed to be imported or accessed, more like ignored.


def block_cache_func():
    return True
