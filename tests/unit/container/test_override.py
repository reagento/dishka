import pytest

from dishka import Provider, Scope, make_container, provide, provide_all
from dishka.entities.validation_settigs import (
    STRICT_VALIDATION,
    ValidationSettings,
)
from dishka.exceptions import (
    ImplicitOverrideDetectedError,
    NothingOverriddenError,
)


def test_no_override_provide() -> None:
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


def test_skip_no_override_provide() -> None:
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


def test_override_provide_ok() -> None:
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


def test_not_override_provide_all() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide_all(int, str)
            + provide_all(int, str)
        )

    with pytest.raises(ImplicitOverrideDetectedError):
        make_container(
            TestProvider(),
            validation_settings=STRICT_VALIDATION,
        )


def test_override_provide_all() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide_all(int, str)
            + provide_all(int, str, override=True)
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

