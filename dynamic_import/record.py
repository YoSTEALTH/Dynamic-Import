from os.path import join
from glob import glob


def add_record(pkg_name, cache_path):
    ''' Add `cache_path` to `site-packages` `RECORD`

        Example
            >>> add_record('pkg',
            ...            '/path/site-packages/pkg/__pycache__/__init__.importer-*.pyc')

        Note
            - When <package> is installed and later uninstalled an lingering 
            `__pycache__/__init__.importer-*.pyc` is left behind! This function
            adds into `RECORD` to remove that lingering file.
    '''
    if (find := '/site-packages/') in cache_path:
        # `/path/python/3.13/lib/python3.13` `pkg/__pycache__/__init__.importer-313.pyc`
        site_path, add_path = cache_path.split(find)
        dist_info = f'{pkg_name}-*.dist-info'  # pkg-*.dist-info
        # b'pkg/__pycache__/__init__.importer-313.pyc,,\r\n'
        write_data = f'{add_path},,\r\n'.encode()
        # ['/path/python/3.13/lib/python3.13/site-packages/<pkg>-<version>.dist-info/RECORD']
        record_path = glob(join(site_path, find[1:], dist_info, 'RECORD'))
        for found in record_path:
            with open(found, 'r+b') as file:
                if write_data not in file.read():
                    file.write(write_data)  # append to end.
                break
