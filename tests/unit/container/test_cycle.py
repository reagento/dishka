from dishka import Provider, Scope, make_container, provide


class A:
    def __init__(self, b: "B"):
        self.b = b

    def foo(self):
        return self.b.foo()

    def bar(self):
        return "A"


class B:
    def __init__(self, a: "A"):
        self.a = a

    def foo(self):
        return "B"

    def bar(self):
        return self.a.bar()


class MyProvider(Provider):
    a = provide(A, scope=Scope.APP)
    b = provide(B, scope=Scope.APP)


def test_cycle():
    with make_container(MyProvider()) as container:
        a = container.get(A)
        assert a.foo() == "B"
        assert a.bar() == "A"
        assert isinstance(a.b, B)
        b = container.get(B)
        assert isinstance(b.a, A)
        assert b.foo() == "B"
        assert b.bar() == "A"
        assert b.a == a
        assert b == a.b
