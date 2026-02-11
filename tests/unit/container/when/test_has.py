import pytest

from dishka import Has, Provider, Scope, make_async_container, make_container


@pytest.mark.parametrize(("register", "value"), [
    (True, "b"),
    (False, "a"),
])
def test_has(*, register: bool, value: str):
    provider = Provider(scope=Scope.APP)
    if register:
        provider.provide(lambda: 42, provides=int)
    provider.provide(lambda: "a", provides=str)
    provider.provide(lambda: "b", provides=str, when=Has(int))

    c = make_container(provider)
    assert c.get(str) == value

@pytest.mark.parametrize(("register", "value"), [
    (True, "b"),
    (False, "a"),
])
@pytest.mark.asyncio
async def test_has_async(*, register: bool, value: str):
    provider = Provider(scope=Scope.APP)
    if register:
        provider.provide(lambda: 42, provides=int)
    provider.provide(lambda: "a", provides=str)
    provider.provide(lambda: "b", provides=str, when=Has(int))

    c = make_async_container(provider)
    assert await c.get(str) == value


@pytest.mark.parametrize(("register", "value"), [
    (True, "b"),
    (False, "a"),
])
def test_has_chained(*, register: bool, value: str):
    provider = Provider(scope=Scope.APP)
    if register:
        provider.provide(lambda: 42, provides=int)
    provider.provide(lambda: 42, provides=float, when=Has(int))
    provider.provide(lambda: "a", provides=str)
    provider.provide(lambda: "b", provides=str, when=Has(float))

    c = make_container(provider)
    assert c.get(str) == value
