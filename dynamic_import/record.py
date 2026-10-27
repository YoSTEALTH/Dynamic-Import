from glob import glob
from os import sep
from os.path import join


SITE = f'{sep}site-packages{sep}'  # Windows: '\site-packages\'


def add_record(pkg_name, cache_path):
    ''' Add `cache_path` to `site-packages` `RECORD`

        Type
            pkg_name:   str
            cache_path: str
            return:     None

        Example
            >>> add_record('pkg',
            ...            '/path/site-packages/pkg/__pycache__/__init__.importer-*.pyc')

        Note
            - When <package> is installed and later uninstalled an lingering
            `__pycache__/__init__.importer-*.pyc` is left behind! This function
            adds into `RECORD` to remove that lingering file.
            - `pkg_name` may be a sub-package (`pkg.sub`); the distribution is looked up
            by the top-level name, falling back to the `RECORD` that lists `pkg/__init__.py`.
    '''
    if SITE not in cache_path:
        return None
    # `/path/python/3.13/lib/python3.13` `pkg/__pycache__/__init__.importer-313.pyc`
    site_path, _, add_path = cache_path.rpartition(SITE)
    site_dir = join(site_path, SITE[1:])
    # b'pkg/__pycache__/__init__.importer-313.pyc,,\r\n'
    write_data = f'{add_path.replace(sep, "/")},,\r\n'.encode()  # `RECORD` paths always use '/'
    if found := find_record(site_dir, pkg_name.partition('.')[0]):
        with open(found, 'r+b') as file:
            content = file.read()
            if write_data not in content:
                if content and not content.endswith(b'\n'):
                    file.write(b'\r\n')
                file.write(write_data)  # append to end.


def find_record(site_dir, top_name):
    ''' Find the `RECORD` file of the distribution that owns `top_name` package

        Type
            site_dir: str
            top_name: str
            return:   str | None

        Example
            >>> find_record('/path/site-packages/', 'pkg')
            '/path/site-packages/pkg-1.2.3.dist-info/RECORD'
    '''
    # fast path: distribution named like the package, e.g: `pkg-1.2.3.dist-info`
    for found in glob(join(site_dir, f'{top_name}-*.dist-info', 'RECORD')):
        return found
    # slow path: distribution named differently, find the `RECORD` that installed `pkg/__init__.py`
    owns = f'{top_name}/__init__.py,'.encode()
    for found in glob(join(site_dir, '*.dist-info', 'RECORD')):
        try:
            with open(found, 'rb') as file:
                for line in file:
                    if line.startswith(owns):
                        return found
        except OSError:
            continue
    return None
