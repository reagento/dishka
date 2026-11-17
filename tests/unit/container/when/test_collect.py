from dishka import Has, Provider, Scope, make_container


def test_collect_when():
    p = Provider(scope=Scope.APP)
    p.provide(lambda: "", provides=str)
    p.provide(lambda: 1, provides=int, when=Has(str))
    p.provide(lambda: 2, provides=int, when=Has(float))
    p.provide(lambda: 3, provides=int)
    p.collect(int)

    c = make_container(p)
    numbers = c.get(list[int])
    assert numbers == [1, 3]


async def provide_async_int() -> int:
    return 4


def test_collect_skips_statically_inactive_async_factory():
    p = Provider(scope=Scope.APP)
    p.provide(lambda: 1, provides=int)
    p.provide(provide_async_int, provides=int, when=Has(float))
    p.collect(int)

    c = make_container(p)
    assert c.get(list[int]) == [1]
