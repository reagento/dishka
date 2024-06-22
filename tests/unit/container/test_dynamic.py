from typing import NewType

from dishka import Container, Provider, Scope, make_container, provide
from dishka.dependency_source import from_context

Request = NewType("Request", int)


class A:
    pass


class A0(A):
    pass


class A1(A):
    pass


class MyProvider(Provider):
    request = from_context(Request, scope=Scope.REQUEST)
    a0 = provide(A0, scope=Scope.APP)
    a1 = provide(A1, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    def get_a(self, container: Container, request: Request) -> A:
        if request == 0:
            return container.get(A0)
        else:
            return container.get(A1)


def test_dynamic():
    container = make_container(MyProvider())
    with container({Request: 0}) as c:
        assert type(c.get(A)) is A0
    with container({Request: 1}) as c:
        assert type(c.get(A)) is A1
