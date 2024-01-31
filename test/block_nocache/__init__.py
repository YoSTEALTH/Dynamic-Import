from dynamic_import import importer


__block1__ = 1111  # this should be allowed to be imported and accessible.

importer(cache=False)

__block2__ = 2222  # this should not be allowed to be imported or accessed, more like ignored.


def block_no_cache_func():
    return True
