import os
import re
import sys
import os.path
import pytest
import subprocess
from dynamic_import.extract import extract_variable, extract_so_variable


def test_extract_variable():
    assert extract_variable('test/basic/__init__.py') == ('DEFINE', 're_import')
    error = "`__all__` values in 'test/basic/skip/bad_all.py' is not string!"
    with pytest.raises(TypeError, match=re.escape(error)):
        extract_variable('test/basic/skip/bad_all.py')


if exec_path := os.path.dirname(sys.executable):
    cythonize = os.path.join(exec_path, 'cythonize')  # '/path/python3' to '/path/cythonize'
    skip_cython = not os.path.exists(cythonize)  # check if cython + cythonize is installed

if (jobs := os.cpu_count()) > 4:
    jobs = 4


@pytest.mark.skipif(skip_cython, reason='Cython/Cythonize NOT Installed!')
def test_extract_so_variable(tmp_dir):
    # create 'pkg' directory
    pkg_path = tmp_dir / 'pkg'
    pkg_path.mkdir()

    # create '__init__.py'
    pyx = pkg_path / '__init__.py'
    pyx.write_text('')

    # create 'one.pyx'
    one_pyx = pkg_path / 'one.pyx'
    one_pyx.write_text('cpdef hello_one(name):\n\treturn f"Hello {name}!"\n\n')

    # create 'two.pyx'
    two_pyx = pkg_path / 'two.pyx'
    two_pyx.write_text('__all__ = ["hello_two"]\ncpdef hello_two(name):\n\treturn f"Hello {name}!"\n\n')

    # create 'three.pyx'
    three_pyx = pkg_path / 'three.pyx'
    three_pyx.write_text('__all__ = "hello_three"\ncpdef hello_three(name):\n\treturn f"Hello {name}!"\n\n')

    # create 'error.pyx'
    error_pyx = pkg_path / 'error.pyx'
    error_pyx.write_text('__all__ = 123\ncpdef hello_error(name):\n\treturn f"Hello {name}!"\n\n')

    # compile all `.so` file
    r = subprocess.run([cythonize, '--inplace', f'--parallel={jobs}',
                        str(one_pyx), str(two_pyx), str(three_pyx), str(error_pyx)],
                       capture_output=True)
    if r.returncode == 0:
        # add 'pkg' to sys path
        sys.path.append(str(pkg_path))

        # one - no `__all__`
        assert extract_so_variable('one') == ['hello_one']
        from pkg.one import hello_one
        assert hello_one('World') == 'Hello World!'

        # two - `__all__ = ["hello_two"]`
        assert extract_so_variable('two') == ['hello_two']
        from pkg.two import hello_two
        assert hello_two('World') == 'Hello World!'

        # three - `__all__ = "hello_three"`
        assert extract_so_variable('three') == ['hello_three']
        from pkg.three import hello_three
        assert hello_three('World') == 'Hello World!'

        # error - `__all__ = 123`
        with pytest.raises(TypeError, match=re.escape("can not parse `__all__` value in 'error'")):
            assert extract_so_variable('error') == ['hello_error']
    elif r.returncode > 0:  # bug
        pytest.skip('Cython bug!!!')
    else:  # error
        raise subprocess.CalledProcessError(returncode=r.returncode, cmd=r.args, stderr=r.stderr)
