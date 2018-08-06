import sys
import os.path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
)
# TODO
#   This "test" needs to be improved with "unittest" or "pytest"
#   before version: 1.0.0 is released.


def run_test():
    # Test-1 - static test
    # --------------------
    try:
        from example.sample import static
        print(static())
    except Exception:
        print('ERROR: Something isn\'t right `from sample import static`')
    print()

    # Test-2 - dynamic test
    # ---------------------
    from example.sample import a, b, c   # noqa
    _ = dir(sys.modules['example.sample'])
    print(
        'Find "a, b, c":', 'a' in _, 'b' in _, 'c' in _
    )
    print(
        'Find "sample.one":',
        {'sample', 'sample.one', 'sample.two'} & sys.modules.keys()
    )
    print(a())
    print(b())
    print(c())
    print()

    # Test-3 - dynamic test
    # ---------------------
    from example.sample import x, y, z  # noqa
    _ = dir(sys.modules['example.sample'])
    print(
        'Find "x, y, z":', 'x' in _, 'y' in _, 'z' in _
    )
    print(x())
    print(y())
    print(z())
    print()

    print(dir(sys.modules['example.sample']))
    print()
    print(dir(sys.modules['example.sample.one']))
    print()
    # v = sys.modules['example.one']
    # print(dir(sys.modules['example.one']))
    # print(v)
    # print(v.__cached__)
    # print(v.__doc__)
    # print(v.__file__)
    # print(v.__loader__)
    # print(v.__name__)
    # print(v.__package__)
    # print(v.__spec__)
    # print()


if __name__ == '__main__':
    run_test()
    #
