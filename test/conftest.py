import os
import os.path
import pytest
import pathlib
import tempfile


@pytest.fixture
def tmp_dir():
    ''' Temporary directory to store test data.

        Example
            >>> test_my_function(tmp_dir)
            ...     # create directory
            ...     # ----------------
            ...     my_dir = tmp_dir / 'my_dir'
            ...     my_dir.mkdir()
            ...
            ...     # create file
            ...     # -----------
            ...     my_file = tmp_dir / 'my_file.ext'
            ...     my_file.write_text('Hello World!!!')

        Note
            - unlike pytest's `tmpdir`, `tmp_path`, ... `tmp_dir` generated
            files & directories are not deleted after 3 runs.
    '''
    tmp_path = f'/tmp/pytest-of-{os.getlogin()}-holder'
    if not os.path.exists(tmp_path):
        os.mkdir(tmp_path)
    return pathlib.Path(tempfile.mkdtemp(dir=tmp_path))
