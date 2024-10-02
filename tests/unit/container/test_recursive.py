from typing import Protocol

from dishka import AnyOf, Provider, Scope, make_container, provide, provide_all


class A1:
    pass


class A2:
    pass


class BProto(Protocol):
    pass


class B(BProto):
    def __init__(self, a1: A1, a2: A2):
        self.a1 = a1
        self.a2 = a2


class C(B):
    pass


def test_provide_class():
    class MyProvider(Provider):
        x = provide(B, scope=Scope.APP, recursive=True)

    container = make_container(MyProvider())
    b = container.get(B)
    assert isinstance(b, B)
    assert isinstance(b.a1, A1)
    assert isinstance(b.a2, A2)


def test_provide_instance():
    provider = Provider(scope=Scope.APP)
    provider.provide(B, recursive=True)
    container = make_container(provider)
    b = container.get(B)
    assert isinstance(b, B)
    assert isinstance(b.a1, A1)
    assert isinstance(b.a2, A2)


def test_provide_any_of():
    provider = Provider(scope=Scope.APP)
    provider.provide(source=B, provides=AnyOf[B, BProto], recursive=True)
    container = make_container(provider)
    b = container.get(B)
    assert isinstance(b, B)
    assert isinstance(b.a1, A1)
    assert isinstance(b.a2, A2)
    assert b is container.get(BProto)


def test_provide_all_class():
    class MyProvider(Provider):
        x = provide_all(B, C, scope=Scope.APP, recursive=True)

    container = make_container(MyProvider(), skip_override=True)
    b = container.get(B)
    assert isinstance(b, B)
    assert isinstance(b.a1, A1)
    assert isinstance(b.a2, A2)
    c = container.get(C)
    assert isinstance(c, B)
    assert isinstance(c.a1, A1)
    assert isinstance(c.a2, A2)


def test_provide_all_instance():
    provider = Provider(scope=Scope.APP)
    provider.provide_all(B, C, recursive=True)
    container = make_container(provider, skip_override=True)
    b = container.get(B)
    assert isinstance(b, B)
    assert isinstance(b.a1, A1)
    assert isinstance(b.a2, A2)
    c = container.get(C)
    assert isinstance(c, B)
    assert isinstance(c.a1, A1)
    assert isinstance(c.a2, A2)
