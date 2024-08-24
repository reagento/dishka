from dishka import Provider, provide_recursive, make_container, Scope


class A1:
    pass


class A2:
    pass


class B:
    def __init__(self, a1: A1, a2: A2):
        self.a1 = a1
        self.a2 = a2


def test_provide_recursive_class():
    class MyProvider(Provider):
        x = provide_recursive(B, scope=Scope.APP)

    container = make_container(MyProvider())
    b = container.get(B)
    assert isinstance(b, B)
    assert isinstance(b.a1, A1)
    assert isinstance(b.a2, A2)
