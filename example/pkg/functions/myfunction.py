from pkg import my_var
# all import names are available at higher level, 
# no need for `from ..example.var import my_var`

__all__ = 'my_function'  # using just string for single name is ok


def my_function():
    return my_var + 1
