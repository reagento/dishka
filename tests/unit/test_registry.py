from dishka.entities.key import DependencyKey
from dishka.entities.scope import Scope
from dishka.provider.make_factory import make_factory
from dishka.registry import Registry


class Abstract: ...


class Provided(Abstract): ...


class Concrete(Provided): ...


def test_get_abstract_factories() -> None:
    registry = Registry(scope=Scope.APP, has_fallback=True)
    privede_key = DependencyKey(Provided, "")
    factory = make_factory(
        provides=Provided,
        scope=Scope.APP,
        source=Provided,
        cache=True,
        is_in_class=False,
        override=False,
    )
    registry.add_factory(factory, privede_key)

    result = registry.get_more_abstract_factories(DependencyKey(Concrete, ""))

    assert result == [factory]


def test_get_concrete_factories() -> None:
    registry = Registry(scope=Scope.APP, has_fallback=True)
    privede_key = DependencyKey(Provided, "")
    factory = make_factory(
        provides=Provided,
        scope=Scope.APP,
        source=Provided,
        cache=True,
        is_in_class=False,
        override=False,
    )
    registry.add_factory(factory, privede_key)

    result = registry.get_more_concrete_factories(DependencyKey(Abstract, ""))

    assert result == [factory]


def test_get_more_concrete_factories_return_empty_for_object() -> None:
    registry = Registry(scope=Scope.APP, has_fallback=True)
    privede_key = DependencyKey(Provided, "")
    factory = make_factory(
        provides=Provided,
        scope=Scope.APP,
        source=Provided,
        cache=True,
        is_in_class=False,
        override=False,
    )
    registry.add_factory(factory, privede_key)

    result = registry.get_more_concrete_factories(DependencyKey(object, ""))

    assert result == []
