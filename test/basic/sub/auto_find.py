# This test is to auto import all the declared assign without the use of `__all__`.
import html  # noqa `html` should not be imported by `dynamic_import`


def my_function():
    return 'nothing here'


var = 123


class MyClass:
    pass


async def my_async_func():
    pass
