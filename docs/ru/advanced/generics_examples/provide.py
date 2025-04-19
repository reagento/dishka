from typing import Generic, TypeVar

from dishka import make_container, Provider, provide, Scope

T = TypeVar("T", bound=int)


class A(Generic[T]):
    pass


class MyProvider(Provider):
    @provide(scope=Scope.APP)
    def make_a(self, t: type[T]) -> A[T]:
        print("Requested type", t)
        return A()


container = make_container(MyProvider())
container.get(A[int])  # printed: Requested type <class 'int'>
container.get(A[bool])  # printed: Requested type <class 'bool'>
container.get(A[str])  # NoFactoryError
