import pytest

from dishka.dependency_source.factory import Factory
from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.key import DependencyKey
from dishka.entities.scope import Scope
from dishka.provider.make_factory import make_factory
from dishka.registry import Registry


class Abstract: ...


class Provided(Abstract): ...


class Concrete(Provided): ...


@pytest.fixture
def factory() -> Factory:
    return make_factory(
        provides=Provided,
        scope=Scope.APP,
        source=Provided,
        cache=True,
        is_in_class=False,
        override=False,
    )


@pytest.fixture
def registry(factory: Factory) -> Registry:
    registry = Registry(scope=Scope.APP, has_fallback=True)

    privede_key = DependencyKey(Provided, DEFAULT_COMPONENT)
    registry.add_factory(factory, privede_key)

    return registry


def test_get_abstract_factories(registry: Registry, factory: Factory) -> None:
    result = registry.get_more_abstract_factories(
        DependencyKey(Concrete, DEFAULT_COMPONENT),
    )

    assert result == [factory]


def test_get_concrete_factories(registry: Registry, factory: Factory) -> None:
    result = registry.get_more_concrete_factories(
        DependencyKey(Abstract, DEFAULT_COMPONENT),
    )

    assert result == [factory]


def test_get_more_concrete_factories_return_empty_for_object(
    registry: Registry,
) -> None:
    result = registry.get_more_concrete_factories(
        DependencyKey(object, DEFAULT_COMPONENT),
    )

    assert result == []
