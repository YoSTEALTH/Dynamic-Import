__all__ = ('rearrange',)


def rearrange(pkg, all):
    ''' Rearrange "all" and produce value to key dict (reverse)

        Type
            pkg:    str
            all:    str, Iterable[str]
            return: Tuple[Dict[str, Tuple[str]], Dict[str, str]]

        Example
            >>> _all, reverse = rearrange(
            ...     'sample',
            ...     {
            ...         '.one': ('a', 'b', 'c'),
            ...         '.two': ('x', 'y', 'z'),
            ...         '.local': 'internals',
            ...         '.sub': {
            ...             '.page': ('e', 'f', 'g'),
            ...             '.name': 'name',
            ...         },
            ...     }
            ... )
            >>> _all
            {
                'sample.one': ('a', 'b', 'c')
                'sample.two': ('x', 'y', 'z')
                'sample.local': ('internals',)
                'sample.sub.page': ('e', 'f', 'g')
                'sample.sub.name': ('name',)
            }
            >>> reverse
            {
                'a': sample.one
                'b': sample.one
                'c': sample.one
                'x': sample.two
                'y': sample.two
                'z': sample.two
                'internals': sample.local
                'e': sample.sub.page
                'f': sample.sub.page
                'g': sample.sub.page
                'name': sample.sub.name
            }
    '''
    _all = {}  # {'test.one': ('a', 'b', 'c'), ...}
    reverse = {}  # {'a': 'test.one', ...}
    for key, value in all.items():
        # Lets convert relative to absolute import!
        # e.g: '.one' -to-> 'test.one'
        key = f'{pkg}{key}' if key[0] == '.' else f'{pkg}.{key}'

        # Lets wrap tuple around str value.
        if isinstance(value, str):
            value = (value,)
        elif isinstance(value, dict):
            # Sub-package recursive
            sub_all, sub_reverse = rearrange(key, value)
            _all.update(sub_all)
            reverse.update(sub_reverse)
            continue  # skip

        # New "__all__" holder
        _all[key] = value

        # Lest reverse assign value to key
        # e.g: {'test.one': ('a', 'b', 'c')} -to-> {'a: 'test.one', ...}
        for attr in value:
            reverse[attr] = key

    return _all, reverse
