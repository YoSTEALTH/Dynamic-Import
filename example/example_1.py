try:
    # Just to see if "noname" is installed
    import noname  # noqa
except ImportError:
    # Localized development test if "noname" isn't installed.
    import sys
    import os.path
    sys.path.insert(
        0,
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    )


if __name__ == '__main__':
    # Static Import #1
    # ----------------
    try:
        from sample import static
        print(static())
    except Exception:
        print('ERROR: Something isn\'t right `from sample import static`')
    print()
    # print(sys.modules.keys())

    # Dynamic Import #1
    # -----------------
    from sample import a, b, c
    _ = dir(sys.modules['sample'])
    find = ('a' in _, 'b' in _, 'c' in _)
    print('Find var "a, b, c":', find)
    if all(find):
        print(a())
        print(b())
        print(c())
    else:
        print('ERROR: Something isn\'t right `from sample import a, b, c`')
    print()
    # print(sys.modules.keys())

    # Dynamic Import #2
    # -----------------
    from sample import x, y, z
    _ = dir(sys.modules['sample'])
    find = ('x' in _, 'y' in _, 'z' in _)
    print('Find var "x, y, z":', find)
    if all(find):
        print(x())
        print(y())
        print(z())
    else:
        print('ERROR: Something isn\'t right `from sample import x, y, z`')
    print()
    # print(sys.modules.keys())
