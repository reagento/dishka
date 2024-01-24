from enum import auto

from dishka import BaseScope


class B:
    def __init__(self, x: int):
        self.x = x

    def __repr__(self):
        return f"<B:{self.x}>"


class CAAAAA:
    def __init__(self):
        pass


class CAAAA:
    def __init__(self, x: CAAAAA):
        pass


class CAAA:
    def __init__(self, x: CAAAA):
        pass


class CAA:
    def __init__(self, x: CAAA):
        pass


class CA:
    def __init__(self, x: CAA):
        pass


class C:
    def __init__(self, x: CA):
        pass


class A:
    def __init__(self, b: B, c: C):
        self.b = b
        self.c = c

    def __repr__(self):
        return f"<<A:{self.b}-{self.c}>>"


class A1(A):
    pass


class MyScope(BaseScope):
    APP = auto()
    REQUEST = auto()


NUMBER = 1000000
