import pytest

from dishka import Provider, Scope, alias, make_container, provide
from dishka.entities.validation_settigs import (
    STRICT_VALIDATION,
    ValidationSettings,
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
            + alias(source=int, provides=float)
            + alias(source=int, provides=float)
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
            + alias(source=int, provides=float)
            + alias(source=int, provides=float)
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
            + alias(source=int, provides=float)
            + alias(source=int, provides=float, override=True)
        )

    make_container(
        TestProvider(),
        validation_settings=STRICT_VALIDATION,
    )


def test_cant_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(int, provides=int)
            + alias(source=int, provides=float, override=True)
        )

    with pytest.raises(NothingOverriddenError) as e:
        make_container(
            TestProvider(),
            validation_settings=STRICT_VALIDATION,
        )
    assert str(e.value)


def test_skip_cant_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(int, provides=int)
            + alias(source=int, provides=float, override=True)
        )

    make_container(
        TestProvider(),
        validation_settings=ValidationSettings(nothing_overridden=False),
    )
