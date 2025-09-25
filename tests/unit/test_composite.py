# ruff: noqa: PGH004, W292, SIM300, T201, RUF100
x = 0.0
a = 4.2

assert x == 0.0
print(3.14 != a)
if x == 0.3: ...
if x          ==       0.42: ...

def foo(a, b):
    return a == b - 0.1

def add(x: float, y: float) -> float:
    return x+y

assert add(1.5, 2) == add(2, 1.5)