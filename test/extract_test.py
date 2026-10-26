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


def test_extract_variable_targets(tmp_dir):
    # 1.1 & 2.4: targets other than a plain name, annotated assignment, `if` blocks.
    file = tmp_dir / 'mod.py'
    file.write_text('import os\n'
                    'x, y = 1, 2\n'
                    '[p, q] = 3, 4\n'
                    'a = b = 5\n'
                    'os.environ["Z"] = "1"\n'
                    'os.name2 = 1\n'
                    'c: int = 6\n'
                    'd: int\n'
                    'if os.name:\n'
                    '    hidden = 7\n'
                    'def func(): pass\n'
                    'async def afunc(): pass\n'
                    'class Klass: pass\n')
    # note: `import os` is not a definition, `hidden` inside `if` is not scanned.
    assert extract_variable(str(file)) == ['x', 'y', 'p', 'q', 'a', 'b', 'c', 'func', 'afunc', 'Klass']


def test_extract_variable_all(tmp_dir):
    file = tmp_dir / 'mod.py'
    file.write_text('__all__ = ["one"]\n__all__ += ["two"]\n__all__ += ("three",)\nother = 1\n')
    assert extract_variable(str(file)) == ['one', 'two', 'three']

    file.write_text('__all__ = ("one",)\n__all__ += ["two"]\n')
    assert extract_variable(str(file)) == ('one', 'two')

    file.write_text('__all__: list[str] = ["one"]\n')
    assert extract_variable(str(file)) == ['one']

    file.write_text('__all__ += ["one"]\n')  # no prior `__all__`
    assert extract_variable(str(file)) == ['one']

    file.write_text('__all__ = [name for name in dir()]\n')
    with pytest.raises(ValueError, match=re.escape('must be a literal list, tuple or string!')):
        extract_variable(str(file))

    file.write_text('__all__ = ["one", 2]\n')
    with pytest.raises(TypeError, match=re.escape('is not string!')):
        extract_variable(str(file))


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
