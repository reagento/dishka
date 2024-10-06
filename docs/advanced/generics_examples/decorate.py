from collections.abc import Iterator
from typing import TypeVar

from dishka import make_container, Provider, provide, Scope, decorate

T = TypeVar("T")


class MyProvider(Provider):
    scope = Scope.APP

    @provide
    def make_int(self) -> int:
        return 1

    @provide
    def make_str(self) -> str:
        return "hello"

    @decorate
    def log(self, a: T, t: type[T]) -> Iterator[T]:
        print("Requested", t, "with value", a)
        yield a
        print("Requested release", a)


container = make_container(MyProvider())
container.get(int)  # Requested int with value 1
container.get(str)  # Requested str with value hello
container.close()
# Requested release object hello
# Requested release object 1

