from unittest.mock import Mock

import pytest

from dishka import (
    DEFAULT_COMPONENT,
    DependencyKey,
    Provider,
    Scope,
    alias,
    make_container,
    provide,
)
from dishka.exceptions import CycleDependenciesError, NoFactoryError


class AliasProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_int(self) -> int:
        return 42

    aliased_complex = alias(source=float, provides=complex)
    aliased_float = alias(source=int, provides=float)


def test_alias():
    container = make_container(AliasProvider())
    assert container.get(float) == container.get(int)


def test_alias_to_alias():
    container = make_container(AliasProvider())
    assert container.get(complex) == container.get(int)


class CycleProvider(Provider):
    a = alias(source=int, provides=bool)
    b = alias(source=bool, provides=float)
    c = alias(source=float, provides=int)


def test_cycle():
    with pytest.raises(CycleDependenciesError):
        make_container(CycleProvider())


def test_missing_factory():
    p1 = Provider()
    p1.alias(source=bool, provides=float)
    p2 = Provider()
    p2.alias(source=int, provides=bool)
    with pytest.raises(NoFactoryError) as e:
        make_container(p1, p2)
    assert e.value.requested == DependencyKey(int, component=DEFAULT_COMPONENT)


def test_implicit():
    mock = Mock(return_value=42)
    provider = Provider(scope=Scope.APP)
    provider.provide(source=lambda: mock(), provides=float | int)
    container = make_container(provider)
    assert container.get(float) == 42
    assert container.get(int) == 42
    mock.assert_called_once()


def test_union_alias():
    provider = Provider(scope=Scope.APP)
    provider.provide(source=lambda: 42, provides=int)
    provider.alias(source=int, provides=float | complex)
    container = make_container(provider)
    assert container.get(float) == 42
    assert container.get(complex) == 42
