import pytest

from dishka import Provider, Scope, make_container, provide, provide_all
from dishka.exceptions import CantOverrideFactoryError, FactoryNotOverrideError


def test_not_override_provide() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(int, provides=int)
            + provide(int, provides=int)
        )

    with pytest.raises(FactoryNotOverrideError):
        make_container(TestProvider())


def test_skip_override_provide() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(int, provides=int)
            + provide(int, provides=int)
        )

    make_container(
        TestProvider(),
        skip_override=True,
    )


def test_override_provide() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(int, provides=int)
            + provide(int, provides=int, override=True)
        )

    make_container(TestProvider())


def test_not_override_provide_all() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide_all(int, str)
            + provide_all(int, str)
        )

    with pytest.raises(FactoryNotOverrideError):
        make_container(TestProvider())


def test_override_provide_all() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide_all(int, str)
            + provide_all(int, str, override=True)
        )

    make_container(TestProvider())


def test_cant_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = provide(int, provides=int, override=True)

    with pytest.raises(CantOverrideFactoryError):
        make_container(TestProvider())


def test_skip_cant_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = provide(int, provides=int, override=True)

    make_container(
        TestProvider(),
        skip_cant_override=True,
    )

