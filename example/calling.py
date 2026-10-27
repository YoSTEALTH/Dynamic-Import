# you can import all 3 names regardless of where they are located as:
# or
import pkg
from pkg import MyClass, my_function, my_var


print(my_var, pkg.my_var is my_var)
print(my_function())
MyClass()
print(dir(pkg))
