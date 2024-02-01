from os.path import normpath, isdir, isabs, isfile, join
from .prep import EXT_SUFFIX


__all__ = 'IMPORTER_CALLED', 'importer_called', 'exclude_file_check', 'exclude_dir_check'
IMPORTER_CALLED = {}  # e.g {'/path/pkg/': {'/path/pkg/sub-dir/'}}


def importer_called(pkg_path):
    ''' Check if `importer()` was previously called.

        Type:
            pkg_path: str
            return:   Union[True, None]

        Example
            >>> importer_called('/path/pkg/')
            None

            # if '/path/pkg/' already exists
            >>> importer_called('/path/pkg/')
            True

            # if '/path/pkg/' already exists and calling `importer()` again from `/path/pkg/sub/pkg/`
            >>> importer_called('/path/pkg/sub/pkg/')
            ImportError

        Note
            - will raises `ImportError()` if `importer()` was previously called from parent module.
            - use `importer(exclude_dir)` to exclude sub-dir if you want to call new `importer()` from sub-dir.
    '''
    if IMPORTER_CALLED:
        for parent, exclude in IMPORTER_CALLED.items():
            if pkg_path.startswith(parent):  # `pkg_path` is within parent directory.
                if pkg_path == parent:
                    return True  # to indicate module should already exist in `sys.modules`
                for each in exclude:
                    # TODO: need to reverse check if sub-directory called `importer()` before parent dir.
                    # sub-directory excluded.
                    if pkg_path.startswith(each):
                        return None
                # sub-directory not excluded.
                _ = f'Can not call `importer()` from {pkg_path!r}, as it was previously called from {parent!r}. ' \
                    'See `help(importer)` for more options.'
                raise ImportError(_)
    IMPORTER_CALLED[pkg_path] = set()


def exclude_file_check(exclude_file, pkg_name, pkg_path):
    '''
        Type
            exclude_file: Union[Tuple[str], str, None]
            pkg_name:     str
            pkg_path:     str
            return:       List[str]

        Example
            >>> exclude_file_check('file.py', 'pkg', '/path/pkg/')
            ['/path/pkg/file.py']

            >>> exclude_file_check(('one.py', 'two.cpython-312-x86_64-linux-gnu.so'), 'pkg', '/path/pkg/')
            ['/path/pkg/one.py', '/path/pkg/two.cpython-312-x86_64-linux-gnu.so']
    '''
    r = []
    if not exclude_file:
        return r

    if isinstance(exclude_file, str):
        exclude_file = (exclude_file,)

    for each in exclude_file:
        if isabs(each):
            error = f'`importer(exclude_file)` received absolute path {each!r} must be relative path.'
            raise ValueError(error)

        if not each.endswith(EXT_SUFFIX):
            ext = f'.{each.split(".", 1)[-1]}'
            sup = ', '.join(EXT_SUFFIX)
            error = f'`importer(exclude_file)` received extension {ext!r} not supported. Only allowed: {sup!r}'
            raise ValueError(error)

        each_file = normpath(join(pkg_path, each))  # '/path/pkg/<file>.<ext>'

        if not isfile(each_file):
            error = f'`importer(exclude_file)` received {each_file!r} which is not an file or does not exist!'
            raise ValueError(error)
        r.append(each_file)
    return r


def exclude_dir_check(exclude_dir, pkg_path, recursive):
    '''
        Type
            exclude_dir: Union[Tuple[str], str, None]
            pkg_path:    str
            recursive:   bool
            return:      List[str]

        Example
            >>> >>> exclude_dir_check('sub-dir', '/path/pkg/', True)
            ['/path/pkg/sub-dir/']

            >>> exclude_dir_check(('sub-dir', 'sub/sub-dir'), '/path/pkg/', True)
            ['/path/pkg/sub-dir/', /path/pkg/sub/sub-dir/']

        Note:
            - Values are appended into `IMPORTER_CALLED`
    '''
    r = []
    if not (recursive and exclude_dir):
        return r

    if isinstance(exclude_dir, str):
        exclude_dir = (exclude_dir,)

    for each in exclude_dir:
        if isabs(each):
            error = f'`importer(exclude_dir)` received absolute path {each!r} must be relative path.'
            raise ValueError(error)

        # normalize path & make sure directory ends with '/'
        each_dir = f'{normpath(join(pkg_path, each))}/'

        if not each_dir.startswith(pkg_path):
            error = f'`importer(exclude_dir)` can not find directory {each_dir!r} within {pkg_path!r}'
            raise ValueError(error)

        if not isdir(each_dir):
            error = f'`importer(exclude_dir)` can not find directory: {each_dir!r}'
            raise ValueError(error)

        IMPORTER_CALLED[pkg_path].add(each_dir)
        r.append(each_dir)
    return r
