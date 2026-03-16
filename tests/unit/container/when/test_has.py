from typing import Any

import pytest

from dishka import (
    Has,
    Provider,
    Scope,
    declare,
    make_async_container,
    make_container,
    provide,
)
from dishka.exceptions import NoActiveFactoryError


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


@pytest.mark.parametrize(
    ("enable_conditional_provider", "successful"), [
        (False, False),
        (True, True),
    ], )
def test_has_with_declared_context_dependency(*, enable_conditional_provider: bool, successful: bool):
    class StringProvider(Provider):
        int_config_declaration = declare(int, scope=Scope.APP)

        @provide(when=Has(int), scope=Scope.APP)
        def setup(self, cfg: int) -> str:
            return "ok"

    class IntProvider(Provider):
        int_config_instance = provide(source=lambda self: 42, provides=int, scope=Scope.APP)

    providers: list[Any] = [StringProvider()]
    if enable_conditional_provider:
        providers.append(IntProvider())

    container = make_container(*providers, context={})

    if successful:
        assert isinstance(container.get(str), str)
    else:
        with pytest.raises(NoActiveFactoryError):
            container.get(str)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("is_async", "register_int", "value"),
    [
        (False, True, "b"),
        (False, False, "a"),
        (True, True, "b"),
        (True, False, "a"),
    ],
)
async def test_provider_declare_method_does_not_make_has_active(
        *, is_async: bool, register_int: bool, value: str
):
    provider = Provider(scope=Scope.APP)
    provider.declare(int)
    provider.provide(lambda: "a", provides=str)
    provider.provide(lambda: "b", provides=str, when=Has(int))

    provider2 = Provider(scope=Scope.APP)
    if register_int:
        provider2.provide(lambda: 42, provides=int)

    if is_async:
        container = make_async_container(provider, provider2, context={})
        assert await container.get(str) == value
    else:
        container = make_container(provider, provider2, context={})
        assert container.get(str) == value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("is_async", "register_ctx", "value"),
    [
        (False, True, "b"),
        (False, False, "a"),
        (True, True, "b"),
        (True, False, "a"),
    ],
)
async def test_from_context_requires_real_context_value_for_has(
        *, is_async: bool, register_ctx: bool, value: str
):
    provider = Provider(scope=Scope.APP)
    provider.from_context(int)
    provider.provide(lambda: "a", provides=str)
    provider.provide(lambda: "b", provides=str, when=Has(int))
    if register_ctx:
        ctx = {int: 42}
    else:
        ctx = {}

    if is_async:
        container = make_async_container(provider, context=ctx)
        assert await container.get(str) == value
    else:
        container = make_container(provider, context=ctx)
        assert container.get(str) == value
