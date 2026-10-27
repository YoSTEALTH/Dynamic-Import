from os import sep
from os.path import normpath, isdir, isabs, isfile, join, splitdrive
from .prep import EXT_SUFFIX


__all__ = 'IMPORTER_CALLED', 'importer_called', 'is_rooted', 'exclude_file_check', 'exclude_dir_check'
IMPORTER_CALLED = {}  # e.g {'/path/pkg/': {'/path/pkg/sub-dir/'}, '/path/flat/': None}
# note: value is the set of excluded sub-directories, or `None` when `recursive=False`
#       (the package did not scan any sub-directory, so all of them are free to call `importer()`).


def importer_called(pkg_path, recursive=True, exclude_dir=()):
    ''' Check if `importer()` was previously called and register this call.

        Type:
            pkg_path:    str
            recursive:   bool
            exclude_dir: Iterable[str]
            return:      True | None

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
            - raises `ImportError()` if `importer()` was previously called from a parent package that
              scanned this directory, or from a sub-directory this call would scan.
            - use `importer(exclude_dir)` or `importer(recursive=False)` in the parent if you want to
              call `importer()` from a sub-directory as well.
    '''
    if (exclude := IMPORTER_CALLED.get(pkg_path, False)) is not False:  # `None` is a valid value
        return True  # to indicate module should already exist in `sys.modules`

    for other, exclude in IMPORTER_CALLED.items():
        if pkg_path.startswith(other):  # `pkg_path` is within `other` (parent) directory.
            if exclude is None or any(pkg_path.startswith(each) for each in exclude):
                continue  # parent did not scan sub-directories, or excluded this one.
            _ = f'Can not call `importer()` from {pkg_path!r}, as it was previously called from {other!r}. ' \
                'See `help(importer)` for more options.'
            raise ImportError(_)
        elif recursive and other.startswith(pkg_path):  # `other` (child) is within `pkg_path`.
            if any(other.startswith(each) for each in exclude_dir):
                continue  # child directory is excluded from this scan.
            _ = f'Can not call `importer()` from {pkg_path!r}, as it was previously called from ' \
                f'sub-directory {other!r}. See `help(importer)` for more options.'
            raise ImportError(_)
    IMPORTER_CALLED[pkg_path] = set(exclude_dir) if recursive else None


def is_rooted(path):
    ''' Path that `join(pkg_path, path)` would not keep inside `pkg_path`

        Type
            path:   str
            return: bool

        Example
            >>> is_rooted('/file.py')
            True

            >>> is_rooted('sub/file.py')
            False

        Note
            - on Windows (3.13+) `isabs()` is `False` for '/file.py' and 'C:file.py', both still leave the package.
    '''
    return isabs(path) or bool(splitdrive(path)[0]) or path.startswith((sep, '/'))


def exclude_file_check(exclude_file, pkg_path):
    '''
        Type
            exclude_file: tuple[str] | str | None
            pkg_path:     str
            return:       list[str]

        Example
            >>> exclude_file_check('file.py', '/path/pkg/')
            ['/path/pkg/file.py']

            >>> exclude_file_check(('one.py', 'two.cpython-312-x86_64-linux-gnu.so'), '/path/pkg/')
            ['/path/pkg/one.py', '/path/pkg/two.cpython-312-x86_64-linux-gnu.so']
    '''
    r = []
    if not exclude_file:
        return r

    if isinstance(exclude_file, str):
        exclude_file = (exclude_file,)

    for each in exclude_file:
        if is_rooted(each):
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
            exclude_dir: tuple[str] | str | None
            pkg_path:    str
            recursive:   bool
            return:      list[str]

        Example
            >>> >>> exclude_dir_check('sub-dir', '/path/pkg/', True)
            ['/path/pkg/sub-dir/']

            >>> exclude_dir_check(('sub-dir', 'sub/sub-dir'), '/path/pkg/', True)
            ['/path/pkg/sub-dir/', /path/pkg/sub/sub-dir/']

        Note:
            - pass the result to `importer_called()` so it is recorded in `IMPORTER_CALLED`.
    '''
    r = []
    if not (recursive and exclude_dir):
        return r

    if isinstance(exclude_dir, str):
        exclude_dir = (exclude_dir,)

    for each in exclude_dir:
        if is_rooted(each):
            error = f'`importer(exclude_dir)` received absolute path {each!r} must be relative path.'
            raise ValueError(error)

        # normalize path & make sure directory ends with '/'
        each_dir = join(normpath(join(pkg_path, each)), '')

        if not each_dir.startswith(pkg_path):
            error = f'`importer(exclude_dir)` can not find directory {each_dir!r} within {pkg_path!r}'
            raise ValueError(error)

        if not isdir(each_dir):
            error = f'`importer(exclude_dir)` can not find directory: {each_dir!r}'
            raise ValueError(error)

        r.append(each_dir)
    return r
