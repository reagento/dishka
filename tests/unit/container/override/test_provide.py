import pytest

from dishka import Provider, Scope, make_container, provide
from dishka.entities.validation_settigs import (
    STRICT_VALIDATION,
    ValidationSettings,
)
from dishka.exceptions.graph import (
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
