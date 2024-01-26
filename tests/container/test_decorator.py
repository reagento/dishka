from dishka import Provider, Scope, provide, make_container
from dishka.provider import decorate


class A:
    pass


class ADecorator:
    def __init__(self, a: A):
        self.a = a


def test_simple():
    class MyProvider(Provider):
        a = provide(A, scope=Scope.APP)
        ad = decorate(ADecorator, provides=A)

    with make_container(MyProvider()) as container:
        print(container.registry)
        a = container.get(A)
        assert isinstance(a, ADecorator)
        assert isinstance(a.a, A)
