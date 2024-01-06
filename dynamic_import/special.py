def special(iterable, error=False):
    ''' Find Special Name

        Type:
            iterable: Iterable[str]
            error:    bool
            yield:    str
            return:   None

        Example
            my_list = ['first', '__name__', 'last']
            >>> for key in special(my_list):
            ...     'first'
            ...     'last'

        Note
            - does not allow special name that start and end with `__`
            - if `error=True` will raise exception if special name is found.
    '''
    for i in iterable:
        if (i[0:2] == '__' == i[-2:]) and (i[2] != '_' != i[-3]):
            if error:
                raise ValueError(f'special name like {i!r} is not supported')
            else:
                continue
        yield i
