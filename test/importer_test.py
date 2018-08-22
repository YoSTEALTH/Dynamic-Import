import sys


def test_static_import():
    from example.sample import static
    assert static() == 'calling static()'
    assert 'example.sample.static' in sys.modules
    assert 'example.sample.one' not in sys.modules
    assert 'example.sample.two' not in sys.modules
    assert 'example.sample.local' not in sys.modules


def test_dynamic_one():
    from example.sample import a, b, c
    assert a() == 'calling a()'
    assert b() == 'calling b()'
    assert c() == 'calling c()'
    assert 'example.sample.static' in sys.modules
    assert 'example.sample.one' in sys.modules
    assert 'example.sample.two' not in sys.modules
    assert 'example.sample.local' not in sys.modules


def test_dynamic_two():
    from example.sample import x, y, z
    assert x() == 'calling x()'
    assert y() == 'calling y()'
    assert z() == 'calling z()'
    assert 'example.sample.static' in sys.modules
    assert 'example.sample.one' in sys.modules
    assert 'example.sample.two' in sys.modules
    assert 'example.sample.local' not in sys.modules


def test_dynamic_local():
    from example.sample import internals
    assert internals() == 'calling internals() -> abcxyz'
    assert 'example.sample.static' in sys.modules
    assert 'example.sample.one' in sys.modules
    assert 'example.sample.two' in sys.modules
    assert 'example.sample.local' in sys.modules


def test_arrange():
    from dynamic_import.importer import _arrange
    _all, _reverse = _arrange(
        'sample',
        {
            '.one': ('a', 'b', 'c'),  # from .one import a, b, c
            '.two': ('x', 'y', 'z'),  # from .two import x, y, z
            '.local': 'internals',    # from .local import internals
        }
    )
    assert _all == {
        'sample.one': ('a', 'b', 'c'),
        'sample.two': ('x', 'y', 'z'),
        'sample.local': ('internals',)
    }
    assert _reverse == {
        'a': 'sample.one',
        'b': 'sample.one',
        'c': 'sample.one',
        'x': 'sample.two',
        'y': 'sample.two',
        'z': 'sample.two',
        'internals': 'sample.local'
    }
