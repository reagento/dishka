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
def test_has_async_sync(*, register: bool, value: str):
    provider = Provider(scope=Scope.APP)
    if register:
        provider.provide(lambda: 42, provides=int)
    provider.provide(lambda: "a", provides=str)
    provider.provide(lambda: "b", provides=str, when=Has(int))

    c = make_async_container(provider)
    assert c.get_sync(str) == value


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


def provide_with_dep(a: int) -> str:
    return str(a)


@pytest.mark.parametrize("scope", [Scope.RUNTIME, Scope.APP])
def test_has_no_dep(scope):
    provider = Provider(scope=scope)
    provider.provide(lambda: "a", provides=str)
    provider.provide(provide_with_dep, provides=str, when=Has(float))

    c = make_container(provider)
    assert c.get(str) == "a"


@pytest.mark.parametrize("scope", [Scope.RUNTIME, Scope.APP])
def test_has_no_dep_nested_scope(scope):
    provider = Provider(scope=scope)
    provider.provide(lambda: "a", provides=str)
    provider.provide(provide_with_dep, provides=str, when=Has(float))

    c = make_container(provider)
    with c() as request_c:
        assert request_c.get(str) == "a"


def test_has_wrong_scope():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "a", provides=str)
    provider.provide(lambda: 1.0, provides=float, scope=Scope.STEP)
    provider.provide(provide_with_dep, provides=str, when=Has(float))

    c = make_container(provider)
    assert c.get(str) == "a"
