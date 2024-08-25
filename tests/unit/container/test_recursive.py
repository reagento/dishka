from dishka import Provider, Scope, make_container, provide, provide_all


class A1:
    pass


class A2:
    pass


class B:
    def __init__(self, a1: A1, a2: A2):
        self.a1 = a1
        self.a2 = a2


class C(B):
    pass


def test_provide_recursive_class():
    class MyProvider(Provider):
        x = provide(B, scope=Scope.APP, recursive=True)

    container = make_container(MyProvider())
    b = container.get(B)
    assert isinstance(b, B)
    assert isinstance(b.a1, A1)
    assert isinstance(b.a2, A2)


def test_provide_recursive_instance():
    provider = Provider(scope=Scope.APP)
    provider.provide(B, recursive=True)
    container = make_container(provider)
    b = container.get(B)
    assert isinstance(b, B)
    assert isinstance(b.a1, A1)
    assert isinstance(b.a2, A2)


def test_provide_all_recursive_class():
    class MyProvider(Provider):
        x = provide_all(B, C, scope=Scope.APP, recursive=True)

    container = make_container(MyProvider())
    b = container.get(B)
    assert isinstance(b, B)
    assert isinstance(b.a1, A1)
    assert isinstance(b.a2, A2)
    c = container.get(C)
    assert isinstance(c, B)
    assert isinstance(c.a1, A1)
    assert isinstance(c.a2, A2)


def test_provide_all_recursive_instance():
    provider = Provider(scope=Scope.APP)
    provider.provide_all(B, C, recursive=True)
    container = make_container(provider)
    b = container.get(B)
    assert isinstance(b, B)
    assert isinstance(b.a1, A1)
    assert isinstance(b.a2, A2)
    c = container.get(C)
    assert isinstance(c, B)
    assert isinstance(c.a1, A1)
    assert isinstance(c.a2, A2)
