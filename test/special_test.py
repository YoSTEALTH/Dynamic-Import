import sys
import pytest
import pathlib
from dynamic_import.special import special


def test_special():
    my_list = ['first', '__name__', '_name', 'name_', 'name', 'name__', '__name', '___name___', '', 'last']
    result = ('first', '_name', 'name_', 'name', 'name__', '__name', '___name___', '', 'last')
    assert tuple(special(my_list)) == result

    with pytest.raises(ValueError, match="special name like '__name__' is not supported"):
        [_ for _ in special(my_list, error=True)]


def test_block():
    with pytest.raises(ImportError, match="cannot import name '__block__' from 'block' .*"):
        from block import __block__  # noqa


def test_block_cache_enabled():
    # cache enabled
    with pytest.raises(ImportError, match="cannot import name '__block2__' from 'block_cache' .*"):
        from block_cache import __block2__  # noqa - not allowed

    from block_cache import __block1__, block_cache_func  # noqa - allowed
    assert __block1__ == 11
    assert block_cache_func() is True

    # run check again so it loads from cache
    from block_cache import __block1__, block_cache_func  # noqa - allowed
    assert __block1__ == 11
    assert block_cache_func() is True
    sys.modules.pop('block_cache')

    # touch file - should remove old cache file and create new.
    pathlib.Path('test/block_cache/__init__.py').touch()
    from block_cache import __block1__, block_cache_func  # noqa


def test_block_cache_disabled():
    # cache disabled
    with pytest.raises(ImportError, match="cannot import name '__block2__' from 'block_nocache' .*"):
        from block_nocache import __block2__    # noqa - not allowed

    from block_nocache import __block1__, block_no_cache_func  # noqa - allowed
    assert __block1__ == 1111
    assert block_no_cache_func() is True
