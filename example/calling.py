# you can import all 3 names regardless of where they are located as:
from pkg import my_var, my_function, MyClass
# or 
import pkg

print(my_var, pkg.my_var is my_var)
print(my_function())
MyClass()
print(dir(pkg))
