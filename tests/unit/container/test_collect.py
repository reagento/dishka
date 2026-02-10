from collections.abc import Sequence

import pytest

from dishka import Provider, Scope, make_container, collect, provide
from dishka.exceptions import InvalidSubfactoryScopeError, NoFactoryError


def test_collect_base():
    p = Provider()
    p.provide(lambda: 1, provides=int, scope=Scope.APP)
    p.provide(lambda: 2, provides=int, scope=Scope.APP)
    p.collect(int)

    c = make_container(p)
    numbers = c.get(list[int])
    assert numbers == [1, 2]
    assert c.get(list[int]) is numbers


def test_collect_provides():
    p = Provider()
    p.provide(lambda: 1, provides=int, scope=Scope.APP)
    p.provide(lambda: 2, provides=int, scope=Scope.APP)
    p.collect(int, provides=Sequence)

    c = make_container(p)
    numbers = c.get(Sequence)
    assert numbers == [1, 2]

def test_collect_on_class():
    p = Provider()
    p.provide(lambda: 1, provides=int, scope=Scope.APP)
    p.provide(lambda: 2, provides=int, scope=Scope.APP)

    class CollectProvider(Provider):
        int_list = collect(int)

    c = make_container(p, CollectProvider())
    numbers = c.get(list[int])
    assert numbers == [1, 2]


def test_collect_scope():
    p = Provider()
    p.provide(lambda: 1, provides=int, scope=Scope.APP)
    p.provide(lambda: 2, provides=int, scope=Scope.APP)
    p.collect(int, scope=Scope.REQUEST)

    c = make_container(p)
    with pytest.raises(NoFactoryError):
        c.get(list[int])

    with c() as request_c:
        numbers = request_c.get(list[int])
    assert numbers == [1, 2]

    with c() as request_c:
        assert request_c.get(list[int]) is not numbers


def test_collect_scope_invalid():
    p = Provider()
    p.provide(lambda: 1, provides=int, scope=Scope.APP)
    p.provide(lambda: 2, provides=int, scope=Scope.REQUEST)
    p.collect(int, scope=Scope.APP)

    with pytest.raises(InvalidSubfactoryScopeError):
        make_container(p)


def test_collect_cache():
    p = Provider()
    p.provide(lambda: 1, provides=int, scope=Scope.APP)
    p.provide(lambda: 2, provides=int, scope=Scope.APP)
    p.collect(int, cache=False)


    c = make_container(p)
    numbers = c.get(list[int])
    assert numbers == [1, 2]
    assert c.get(list[int]) is not numbers


def test_collect_empty():
    p = Provider()
    p.collect(int)
    c = make_container(p)
    assert c.get(list[int]) == []


def list_decorator(a: list[int]) -> list[int]:
    return [*a, 42]


def test_collect_decorate():
    p = Provider()
    p.collect(int)
    p.decorate(list_decorator)
    c = make_container(p)
    assert c.get(list[int]) == [42]

def test_collect_alias():
    p = Provider()
    p.collect(int)
    p.alias(list[int], provides=Sequence[int])
    c = make_container(p)
    assert c.get(Sequence[int]) == []


def test_collect_as_dep():
    p = Provider(scope=Scope.APP)
    p.provide(lambda: 1, provides=int)
    p.provide(lambda: 2, provides=int)
    p.collect(int)

    class DepProvider(Provider):
        @provide(scope=Scope.APP)
        def foo(self, nums: list[int]) -> tuple[int, ...]:
            return tuple(nums)

    c = make_container(p, DepProvider())
    assert c.get(tuple[int, ...]) == (1, 2)