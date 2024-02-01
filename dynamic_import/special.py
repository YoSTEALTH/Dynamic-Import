def special(iterable, error=False):
    ''' Find Special Name

        Type:
            iterable: Iterable[str]
            error:    bool
            yield:    str
            return:   None

        Example
            my_list = ['first', '__name__', 'last']
            >>> for name in special(my_list):
            ...     'first'
            ...     'last'

            >>> for name in special(my_list, error=True):
            ...     ValueError: special name like '__name__' is not supported

        Note
            - special name are ignored by default. e.g: `__something__`
            - if `error=True` will raise exception if special name is found.
    '''
    for name in iterable:
        if (name[0:2] == '__' == name[-2:]) and (name[2] != '_' != name[-3]):
            if error:
                raise ValueError(f'special name like {name!r} is not supported')
            continue
        yield name
