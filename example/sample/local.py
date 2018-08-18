from sample.one import a
from sample.two import x


def o():
    # call locally imported functions
    print('inside "local.py" calling a() and x() insdie o()')
    print(a())
    print(x())
