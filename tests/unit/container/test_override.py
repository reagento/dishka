import pytest

from dishka import Provider, Scope, make_container, provide, provide_all
from dishka.exceptions import NotOverrideFactoryError


def test_not_override_provide() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(source=int, provides=int)
            + provide(source=int, provides=int)
        )

    with pytest.raises(NotOverrideFactoryError):
        make_container(TestProvider())


def test_override_provide() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(source=int, provides=int)
            + provide(source=int, provides=int, override=True)
        )

    make_container(TestProvider())


def test_not_override_provide_all() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide_all(int, str)
            + provide_all(int, str)
        )

    with pytest.raises(NotOverrideFactoryError):
        make_container(TestProvider())


def test_override_provide_all() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide_all(int, str)
            + provide_all(int, str, overrides=True)
        )

    make_container(TestProvider())


def test_not_override_provide_all_and_provide() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(source=int, provides=int)
            + provide_all(int, str)
        )

    with pytest.raises(NotOverrideFactoryError):
        make_container(TestProvider())


def test_override_provide_all_and_provide() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(source=int, provides=int)
            + provide_all(int, str, overrides=True)
        )

    make_container(TestProvider())


def test_not_override_provide_and_provide_all() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide_all(int, str)
            + provide(source=int, provides=int)
        )

    with pytest.raises(NotOverrideFactoryError):
        make_container(TestProvider())


def test_override_provide_provide_all() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide_all(int, str)
            + provide(source=int, provides=int, override=True)
        )

    make_container(TestProvider())


def test_override_different_scopes() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(source=int, provides=int, override=True)
            + provide(
                source=int,
                provides=int,
                override=True,
                scope=Scope.REQUEST,
            )
        )

    make_container(TestProvider())
