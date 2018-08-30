import sys
from dynamic_import.importer import importer, rearrange


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


def test_sub_page():
    from example.sample import e, f, g
    assert e() == 'calling e()'
    assert f() == 'calling f()'
    assert g() == 'calling g()'


def test_sub_name():
    from example.sample import name
    assert name() == 'calling name()'


def test_rearrange():
    __all__ = {
        'one': ('a', 'b', 'c'),  # from .one import a, b, c
        'two': ('x', 'y', 'z'),  # from .two import x, y, z
        'local': 'internals',    # from .local import internals
        'sub': {
            'page': ('e', 'f', 'g'),  # from .sub.page import e, f, g
            'name': 'name',           # from .sub.name import name
        },
    }
    find_all = {
        'sample.one': ('a', 'b', 'c'),
        'sample.two': ('x', 'y', 'z'),
        'sample.local': ('internals',),
        'sample.sub.page': ('e', 'f', 'g'),
        'sample.sub.name': ('name',)
    }
    find_reverse = {
        'a': 'sample.one',
        'b': 'sample.one',
        'c': 'sample.one',
        'x': 'sample.two',
        'y': 'sample.two',
        'z': 'sample.two',
        'internals': 'sample.local',
        'e': 'sample.sub.page',
        'f': 'sample.sub.page',
        'g': 'sample.sub.page',
        'name': 'sample.sub.name'
    }
    _all, _reverse = rearrange('sample', __all__)
    assert _all == find_all
    assert _reverse == find_reverse

    # Modules with "."
    __all__ = {
        '.one': ('a', 'b', 'c'),  # from .one import a, b, c
        '.two': ('x', 'y', 'z'),  # from .two import x, y, z
        '.local': 'internals',    # from .local import internals
        '.sub': {
            '.page': ('e', 'f', 'g'),  # from .sub.page import e, f, g
            '.name': 'name',           # from .sub.name import name
        }
    }
    _all, _reverse = rearrange('sample', __all__)
    assert _all == find_all
    assert _reverse == find_reverse


def test_outside_init():
    # 'ImportError: "importer()" must be used/called inside "__init__.py" file'
    try:
        importer('example.sample', {'one': ('a', 'b', 'c')})
    except ImportError:
        assert True
    else:
        assert False
