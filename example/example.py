# flake8: noqa
# Note
#   - Call example using `python3 example.py` or `python3 -m example`

# Static Import #1
# ----------------
from sample import static
# Only "sample" & "sample.static" modules are loaded at this point.
print(static())
print()


# Dynamic Import #1
# -----------------
from sample import a, b, c
# Now "sample", "sample.static" & "sample.one" modules are loaded at this point.
print(a())
print(b())
print(c())
print()

# Dynamic Import #2
# -----------------
from sample import x, y, z
# All "sample", "sample.static", "sample.one" & "sample.two" modules are loaded.
print(x())
print(y())
print(z())
print()

# Dynamic Import #3
# -----------------
from sample import internals
# This is to demonstrate you can relatively import one module from another module.
print(internals())
print()

# Sub-page Import #1
# ------------------
from sample import e, f, g
# This demonstrates you can use nested sub-dir and use main module to import from.
print(e())
print(f())
print(g())
print()

# Sub-page Import #2
# ------------------
from sample import name
# Another sub-dir example
print(name())
print()
