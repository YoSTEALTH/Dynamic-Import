from os.path import dirname, abspath, isdir


__all__ = 'IMPORTER_CALLED', 'importer_called', 'exclude_directory'
IMPORTER_CALLED = {}  # e.g {'/path/pkg/': ['/path/pkg/sub-dir/']}


def importer_called(pkg_path):
    ''' Check if `importer()` was previously called.

        Type:
            pkg_path: str
            return:   None

        Example
            >>> importer_called('/path/pkg/__init__.py')
            None

        Note
            - will raises `ImportError()` if `importer()` was previously called.
    '''
    pkg_dir = f'{dirname(pkg_path)}/'  # `startswith()` will not find correctly without '/'
    if IMPORTER_CALLED:
        for parent, exclude in IMPORTER_CALLED.items():
            if pkg_dir.startswith(parent):  # `pkg_path` is within parent directory.
                for each in exclude:
                    # TODO: need to reverse check if sub-directory called `importer()` before parent dir.
                    # sub-directory excluded.
                    if pkg_dir.startswith(each):
                        return None
                # sub-directory not excluded.
                parent_path = f'{parent}__init__.py'
                _ = f'Can not call `importer()` from {pkg_path!r}, as it was previously called from {parent_path!r}. ' \
                    'See `help(importer)` for more options.'
                raise ImportError(_)
    else:
        IMPORTER_CALLED[pkg_dir] = []


def exclude_directory(exclude_dir, pkg_path):
    '''
        Type
            exclude_dir: Union[Tuple[str], str, None]
            pkg_path:    str
            return:      List[str]

        Example
            >>> exclude_directory(['/path/pkg/one', '/path/pkg/two/'], '/path/pkg/__init__.py')
            [...]

        Note:
            - Values are appended into `IMPORTER_CALLED`
    '''
    r = []
    if not exclude_dir:
        return r

    if isinstance(exclude_dir, str):
        exclude_dir = (exclude_dir,)

    pkg_dir = f'{dirname(pkg_path)}/'
    
    for each in exclude_dir:
        each_dir = abspath(each)
        if not exclude_dir.startswith(pkg_dir):
            _ = f'`importer(exclude)` received exclude directory {each_dir!r} which is not within {pkg_dir!r}'
            raise ValueError(_)
        if not isdir(each_dir):
            _ = f'`importer(exclude)` received {each_dir!r} which is not a directory!'
            raise ValueError(_)
        if each_dir.endswith('/'):
            IMPORTER_CALLED[pkg_dir].append(each_dir)
            r.append(each_dir)
        else:  # make sure directory ends with '/'
            each_dir = f'{each_dir}/'
            IMPORTER_CALLED[pkg_dir].append(each_dir)
            r.append(each_dir)
    return r
