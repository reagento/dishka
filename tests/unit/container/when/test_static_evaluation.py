import pytest

from dishka import (
    Has,
    Marker,
    Provider,
    Scope,
    make_async_container,
    make_container,
)


def test_static_strips_inactive_provider():
    provider = Provider(scope=Scope.APP)

    def activator() -> bool:
        return False

    provider.activate(activator, Marker("Feature"))
    provider.provide(lambda: "default", provides=int)
    provider.provide(lambda: 42, provides=int, when=Marker("Feature"))

    container = make_container(provider)
    assert container.get(int) == "default"


def test_static_keeps_active_provider():
    provider = Provider(scope=Scope.APP)

    def activator() -> bool:
        return True

    provider.activate(activator, Marker("Feature"))
    provider.provide(lambda: "default", provides=int)
    provider.provide(lambda: 42, provides=int, when=Marker("Feature"))

    container = make_container(provider)
    assert container.get(int) == 42


@pytest.mark.asyncio
async def test_dynamic_activator_evaluated_at_runtime():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: True, provides=bool)

    async def async_activator(flag: bool) -> bool:  # noqa: FBT001
        return flag

    provider.activate(async_activator, Marker("Async"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(lambda: "async", provides=str, when=Marker("Async"))

    container = make_async_container(provider)
    result = await container.get(str)
    assert result == "async"
    await container.close()


def test_has_static_when_type_not_registered():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: "default", provides=str)
    provider.provide(lambda: "with_int", provides=str, when=Has(int))

    container = make_container(provider)
    assert container.get(str) == "default"


def test_has_static_when_type_registered():
    provider = Provider(scope=Scope.APP)
    provider.provide(lambda: 42, provides=int)
    provider.provide(lambda: "default", provides=str)
    provider.provide(lambda: "with_int", provides=str, when=Has(int))

    container = make_container(provider)
    assert container.get(str) == "with_int"


@pytest.mark.parametrize(
    ("context", "expected"),
    [
        pytest.param({int: 42}, "has_int", id="context_present"),
        pytest.param({}, "default", id="context_absent"),
    ],
)
def test_has_static_with_from_context(context, expected):
    provider = Provider(scope=Scope.APP)
    provider.from_context(provides=int)
    provider.provide(lambda: "default", provides=str)
    provider.provide(lambda: "has_int", provides=str, when=Has(int))

    container = make_container(provider, context=context)
    assert container.get(str) == expected


def test_multiple_static_activators():
    provider = Provider(scope=Scope.APP)

    def activator_a() -> bool:
        return True

    def activator_b() -> bool:
        return False

    provider.activate(activator_a, Marker("A"))
    provider.activate(activator_b, Marker("B"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(lambda: "a", provides=str, when=Marker("A"))
    provider.provide(lambda: "b", provides=str, when=Marker("B"))

    container = make_container(provider)
    assert container.get(str) == "a"


def test_static_with_context_value():
    provider = Provider(scope=Scope.APP)
    provider.from_context(provides=bool)

    def activator(flag: bool) -> bool:  # noqa: FBT001
        return flag

    provider.activate(activator, Marker("Flag"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(lambda: "conditional", provides=str, when=Marker("Flag"))

    container = make_container(provider, context={bool: True})
    assert container.get(str) == "conditional"


def test_static_strips_when_context_false():
    provider = Provider(scope=Scope.APP)
    provider.from_context(provides=bool)

    def activator(flag: bool) -> bool:  # noqa: FBT001
        return flag

    provider.activate(activator, Marker("Flag"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(lambda: "conditional", provides=str, when=Marker("Flag"))

    container = make_container(provider, context={bool: False})
    assert container.get(str) == "default"


def test_static_activator_with_and_condition():
    provider = Provider(scope=Scope.APP)

    def activator_a() -> bool:
        return True

    def activator_b() -> bool:
        return True

    provider.activate(activator_a, Marker("A"))
    provider.activate(activator_b, Marker("B"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(
        lambda: "both_active",
        provides=str,
        when=Marker("A") & Marker("B"),
    )

    container = make_container(provider)
    assert container.get(str) == "both_active"


def test_static_activator_with_or_condition():
    provider = Provider(scope=Scope.APP)

    def activator_a() -> bool:
        return False

    def activator_b() -> bool:
        return True

    provider.activate(activator_a, Marker("A"))
    provider.activate(activator_b, Marker("B"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(
        lambda: "one_active",
        provides=str,
        when=Marker("A") | Marker("B"),
    )

    container = make_container(provider)
    assert container.get(str) == "one_active"


def test_static_activator_with_not_condition():
    provider = Provider(scope=Scope.APP)

    def activator() -> bool:
        return True

    provider.activate(activator, Marker("A"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(
        lambda: "not_a",
        provides=str,
        when=~Marker("A"),
    )

    container = make_container(provider)
    assert container.get(str) == "default"


def test_static_with_explicit_start_scope():
    provider = Provider(scope=Scope.APP)

    def activator() -> bool:
        return True

    provider.activate(activator, Marker("Feature"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(lambda: "active", provides=str, when=Marker("Feature"))

    container = make_container(provider, start_scope=Scope.APP)
    assert container.get(str) == "active"


def test_static_activator_with_keyword_arg():
    provider = Provider(scope=Scope.APP)
    provider.from_context(provides=bool)

    def activator(*, flag: bool) -> bool:
        return flag

    provider.activate(activator, Marker("KW"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(lambda: "kw_active", provides=str, when=Marker("KW"))

    container = make_container(provider, context={bool: True})
    assert container.get(str) == "kw_active"


def test_and_condition_short_circuits_on_false():
    provider = Provider(scope=Scope.APP)

    def activator_a() -> bool:
        return False

    def activator_b() -> bool:
        return True

    provider.activate(activator_a, Marker("A"))
    provider.activate(activator_b, Marker("B"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(
        lambda: "both_active",
        provides=str,
        when=Marker("A") & Marker("B"),
    )

    container = make_container(provider)
    assert container.get(str) == "default"


def test_or_condition_short_circuits_on_true():
    provider = Provider(scope=Scope.APP)

    def activator_a() -> bool:
        return True

    def activator_b() -> bool:
        return False

    provider.activate(activator_a, Marker("A"))
    provider.activate(activator_b, Marker("B"))
    provider.provide(lambda: "default", provides=str)
    provider.provide(
        lambda: "one_active",
        provides=str,
        when=Marker("A") | Marker("B"),
    )

    container = make_container(provider)
    assert container.get(str) == "one_active"
