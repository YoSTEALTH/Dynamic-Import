# Static Import #1
# ----------------
from sample import static
print(static())
print()

# Dynamic Import #1
# -----------------
from sample import a, b, c  # noqa
print(a())
print(b())
print(c())
print()

# Dynamic Import #2
# -----------------
from sample import x, y, z  # noqa
print(x())
print(y())
print(z())
print()

# Dynamic Import #3
# -----------------
from sample import internals  # noqa
print(internals())
