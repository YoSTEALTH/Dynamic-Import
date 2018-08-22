from .one import a, b, c
from .two import x, y, z


def internals():
    r = []

    if a():
        r.append('a')

    if b():
        r.append('b')

    if c():
        r.append('c')

    if x():
        r.append('x')

    if y():
        r.append('y')

    if z():
        r.append('z')

    return 'calling internals() -> ' + ''.join(r)
