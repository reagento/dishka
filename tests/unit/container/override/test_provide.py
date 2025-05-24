import pytest

from dishka import (
    STRICT_VALIDATION,
    Provider,
    Scope,
    ValidationSettings,
    make_container,
    provide,
)
from dishka.exceptions import (
    ImplicitOverrideDetectedError,
    NothingOverriddenError,
)


def test_no_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(int, provides=int)
            + provide(int, provides=int)
        )

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
            provide(int, provides=int)
            + provide(int, provides=int)
        )

    make_container(
        TestProvider(),
        validation_settings=ValidationSettings(implicit_override=False),
    )


def test_override_ok() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(int, provides=int)
            + provide(int, provides=int, override=True)
        )

    make_container(
        TestProvider(),
        validation_settings=STRICT_VALIDATION,
    )


def test_cant_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = provide(int, provides=int, override=True)

    with pytest.raises(NothingOverriddenError) as e:
        make_container(
            TestProvider(),
            validation_settings=STRICT_VALIDATION,
        )
    assert str(e.value)


def test_skip_cant_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = provide(int, provides=int, override=True)

    make_container(
        TestProvider(),
        validation_settings=ValidationSettings(nothing_overridden=False),
    )


@pytest.mark.parametrize(
    ("scope1", "scope2"),
    [
        (Scope.APP, Scope.REQUEST),
        (Scope.REQUEST, Scope.APP),
        (Scope.APP, Scope.APP),
    ],
)
def test_override_different_scope(scope1: Scope, scope2: Scope) -> None:
    p1 = Provider(scope1)
    p1.provide(lambda: 1, provides=int)

    @p1.decorate
    def decorate_int(a: int) -> int:
        return -a

    p2 = Provider(scope2)
    p2.provide(lambda: 2, provides=int)
    container = make_container(p1, p2)
    with container() as request_container:
        assert request_container.get(int) == 2
