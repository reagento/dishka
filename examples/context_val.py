from typing import Annotated

from dishka import Provider, provide, make_container, Scope, FromComponent, \
    Container


class A:
    def __init__(self, a: int) -> None:
        pass


class Provider1(Provider):
    scope = Scope.APP

    @provide
    def a1(self, a: float) -> int: ...

    @provide
    def a2(self, a: bool) -> float: ...

    @provide
    def a3(self,
           a: Annotated[complex, FromComponent("provider2")]) -> bool: ...

    @provide
    def a4(self, a: A) -> complex: ...


class Provider2(Provider):
    scope = Scope.APP
    component = "provider2"

    @provide
    def a1(self, a: Container) -> complex: ...


c = make_container(Provider1(), Provider2())
c.get(type)
