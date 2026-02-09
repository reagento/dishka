from dishka import Provider, Scope, Has, make_container


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
