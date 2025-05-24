import pytest

from dishka import (
    STRICT_VALIDATION,
    Provider,
    Scope,
    ValidationSettings,
    from_context,
    make_container,
)
from dishka.exceptions import (
    ImplicitOverrideDetectedError,
    NothingOverriddenError,
)


def test_no_override() -> None:
    class TestProvider(Provider):
        app_int = from_context(int, scope=Scope.APP)
        request_int = from_context(int, scope=Scope.REQUEST)

    with pytest.raises(ImplicitOverrideDetectedError) as e:
        make_container(
            TestProvider(),
            validation_settings=STRICT_VALIDATION,
        )
    assert str(e.value)


def test_skip_no_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            from_context(int)
            + from_context(int)
        )

    make_container(
        TestProvider(),
        validation_settings=ValidationSettings(implicit_override=False),
    )


def test_override_ok() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            from_context(int)
            + from_context(int, override=True)
        )

    make_container(
        TestProvider(),
        validation_settings=STRICT_VALIDATION,
    )


def test_cant_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = from_context(int, override=True)

    with pytest.raises(NothingOverriddenError) as e:
        make_container(
            TestProvider(),
            validation_settings=STRICT_VALIDATION,
        )
    assert str(e.value)


def test_skip_cant_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = from_context(int, override=True)

    make_container(
        TestProvider(),
        validation_settings=ValidationSettings(nothing_overridden=False),
    )


@pytest.mark.parametrize(
    ("scope1", "scope2", "app_context", "req_context"),
    [
        (Scope.APP, Scope.REQUEST, {}, {int: 2}),
        (Scope.REQUEST, Scope.APP, {int: 2}, {}),
        (Scope.APP, Scope.APP, {}, {int: 2}),
    ],
)
def test_override_to_context(
        scope1: Scope, scope2: Scope, app_context: dict, req_context: dict,
) -> None:
    p1 = Provider(scope1)
    p1.provide(lambda: 1, provides=int)

    @p1.decorate
    def decorate_int(a: int) -> int:
        return -a

    p2 = Provider(scope2)
    p2.from_context(provides=int)
    container = make_container(p1, p2, context=app_context)
    with container(context=req_context) as request_container:
        assert request_container.get(int) == 2


@pytest.mark.parametrize(
    ("scope1", "scope2"),
    [
        (Scope.APP, Scope.REQUEST),
        (Scope.REQUEST, Scope.APP),
        (Scope.APP, Scope.APP),
    ],
)
def test_override_context_to_provide(scope1: Scope, scope2: Scope) -> None:
    p1 = Provider(scope1)
    p1.from_context(provides=int)

    p2 = Provider(scope2)
    p2.provide(lambda: 2, provides=int)
    container = make_container(p1, p2)
    with container() as request_container:
        assert request_container.get(int) == 2
