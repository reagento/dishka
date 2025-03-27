from typing import Generic, TypeVar

import pytest

from dishka import Provider, Scope, make_container, provide
from dishka.exceptions import GraphMissingFactoryError

T = TypeVar("T")
U = TypeVar("U")


class Base(Generic[T]):
    def __init__(self, y: T):
        self.y = y


class ReplaceInit(Base[str], Generic[T]):
    def __init__(self, x: T):
        super().__init__("hello")
        self.x = x


class A(Generic[T]):
    def __init__(self, x: T, *, y: T):
        assert x == y
        self.x = x

    def __eq__(self, other):
        return isinstance(other, A) and other.x == self.x


class B(A[U], Generic[U]):
    pass


@pytest.mark.parametrize(
    "cls", [A, B, ReplaceInit],
)
def test_concrete_generic(cls):
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_int(self) -> int:
            return 42

        a = provide(cls[int])

    container = make_container(MyProvider())
    a = container.get(cls[int])
    assert isinstance(a, cls)
    assert a.x == 42


class C(A[int]):
    pass


def test_concrete_child():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_int(self) -> int:
            return 42

        a = provide(C)

    container = make_container(MyProvider())
    a = container.get(C)
    assert isinstance(a, C)
    assert a.x == 42


def test_generic_class():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_int(self) -> int:
            return 42

        a = provide(A)

    container = make_container(MyProvider())
    a = container.get(A[int])
    assert isinstance(a, A)
    assert a.x == 42


def test_bare_generic_method():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def a(self) -> A:
            return A(42, y=42)

    container = make_container(MyProvider())
    a = container.get(A)
    assert isinstance(a, A)
    assert a.x == 42


def test_generic_func():
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_int(self) -> int:
            return 42

        @provide
        def a(self, param: T) -> A[T]:
            return A(param, y=param)

    container = make_container(MyProvider())
    a = container.get(A[int])
    assert isinstance(a, A)
    assert a.x == 42


class Event:
    pass


EventsT = TypeVar("EventsT")


class EventEmitter(Generic[EventsT]):
    pass


class EventEmitterImpl(EventEmitter[EventsT]):
    def __init__(self, x: EventsT) -> None:
        pass


def factory(event_emitter: EventEmitter[Event]) -> int:
    return 1


def factory_invalid(event_emitter: EventEmitter[str]) -> int:
    return 1


def test_generic_validation_ok():
    provider = Provider(scope=Scope.APP)
    provider.provide(EventEmitterImpl, provides=EventEmitter)
    provider.provide(source=lambda: None, provides=Event)
    provider.provide(factory)
    assert make_container(provider)


def test_generic_validation_typevar_ok():
    provider = Provider(scope=Scope.APP)
    provider.provide(EventEmitterImpl[EventsT], provides=EventEmitter[EventsT])
    provider.provide(source=lambda: None, provides=Event)
    provider.provide(factory)
    assert make_container(provider)


def test_generic_validation_fail():
    provider = Provider(scope=Scope.APP)
    provider.provide(EventEmitterImpl, provides=EventEmitter)
    provider.provide(factory_invalid)
    with pytest.raises(GraphMissingFactoryError):
        assert make_container(provider)


def type_var_factory(type_: type[T]) -> EventEmitter[T]:
    return type_


def test_passing_type_var():
    provider = Provider(scope=Scope.APP)
    provider.provide(type_var_factory)
    container = make_container(provider)
    assert container.get(EventEmitter[int]) is int


def parametrized_param_func(param: A[T]) -> EventEmitter[T]:
    return param.x


def test_func_with_generic_params():
    provider = Provider(scope=Scope.APP)
    provider.provide(parametrized_param_func)
    provider.provide(lambda: A(42, y=42), provides=A[T])
    container = make_container(provider)
    assert container.get(EventEmitter[int]) == 42


Tint = TypeVar("Tint", bound=int)


def type_var_decorator(
    type_: type[Tint], em: EventEmitter[Tint], obj: Tint,
) -> Tint:
    return type_, em, obj


def test_passing_type_var_decorator():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: A(42, y=42), provides=int)
    provider.provide(lambda: 1, provides=EventEmitter[T])
    provider.decorate(type_var_decorator)
    container = make_container(provider)
    assert container.get(int) == (int, 1, A(42, y=42))


def func_with_type(param: type[T], param2: type[int]) -> A[T]:
    return param, param2


def test_provide_type_non_generic():
    provider = Provider(scope=Scope.APP)
    provider.provide(func_with_type, scope=Scope.REQUEST)
    provider.provide(lambda: bool, provides=type[int])
    container = make_container(provider)
    with container() as c:
        assert c.get(A[str]) == (str, bool)
        assert c.get(A[int]) == (bool, bool)


T2 = TypeVar("T2")
class Multi(Generic[T, T2]):
    pass

def func_with_at2(b: type[T2]) -> Multi[int, A[T2]]:
    return b

def func_with_t2(b: type[T2]) -> Multi[int, T2]:
    return b


def func_with_t2t(b: type[T2], a: type[T]) -> Multi[A[T], T2]:
    return b, a


def test_provide_partial_generic():
    provider = Provider(scope=Scope.APP)
    provider.provide(func_with_t2)
    container = make_container(provider)
    assert container.get(Multi[int, bool]) is bool

    provider = Provider(scope=Scope.APP)
    provider.provide(func_with_at2)
    container = make_container(provider)
    assert container.get(Multi[int, A[bool]]) is bool

    provider = Provider(scope=Scope.APP)
    provider.provide(func_with_t2t)
    container = make_container(provider)
    assert container.get(Multi[A[int], A[bool]]) == (A[bool], int)
