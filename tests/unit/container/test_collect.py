import pytest

from dishka import Provider, Scope, make_container
from dishka.exceptions import NoFactoryError


def test_collect_factories():
    p = Provider()
    p.provide(lambda: 1, provides=int, scope=Scope.APP)
    p.provide(lambda: 2, provides=int, scope=Scope.APP)
    p.collect(int)

    c = make_container(p)
    numbers = c.get(list[int])
    assert numbers == [1, 2]
    assert c.get(list[int]) is numbers


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


def test_collect_cache():
    p = Provider()
    p.provide(lambda: 1, provides=int, scope=Scope.APP)
    p.provide(lambda: 2, provides=int, scope=Scope.APP)
    p.collect(int, cache=False)


    c = make_container(p)
    numbers = c.get(list[int])
    assert numbers == [1, 2]
    assert c.get(list[int]) is not numbers