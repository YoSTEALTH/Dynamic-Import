import sys

# just like normal import if `__all__` is not defined, `my_var` will be included.
# Also `sys` will not be included.

my_var = sys.version_info.major
