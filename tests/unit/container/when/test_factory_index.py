from dishka import Scope
from dishka.dependency_source.factory import Factory
from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.factory_index import FactoryIndex


def _make_factory(
    type_hint: type,
    factory_type: FactoryType = FactoryType.FACTORY,
    scope: Scope = Scope.APP,
    component: str = DEFAULT_COMPONENT,
) -> Factory:
    return Factory(
        dependencies=[],
        kw_dependencies={},
        source=lambda: None,
        provides=DependencyKey(type_hint, component),
        scope=scope,
        type_=factory_type,
        is_to_bind=False,
        cache=True,
        when_override=None,
        when_active=None,
        when_component=None,
        when_dependencies={},
    )


def test_contains_returns_true_for_registered_key():
    factory = _make_factory(int)
    key = DependencyKey(int, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)

    assert key in index


def test_contains_returns_false_for_unregistered_key():
    factory = _make_factory(int)
    int_key = DependencyKey(int, DEFAULT_COMPONENT)
    str_key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {int_key: [factory]}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)

    assert str_key not in index


def test_contains_returns_false_for_empty_factory_list():
    key = DependencyKey(int, DEFAULT_COMPONENT)
    processed = {key: []}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)

    assert key not in index


def test_get_returns_factory_for_registered_key():
    factory = _make_factory(int)
    key = DependencyKey(int, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)

    assert index.get(key) is factory


def test_get_returns_none_for_unregistered_key():
    factory = _make_factory(int)
    int_key = DependencyKey(int, DEFAULT_COMPONENT)
    str_key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {int_key: [factory]}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)

    assert index.get(str_key) is None


def test_get_returns_last_factory_when_multiple_registered():
    first = _make_factory(int)
    second = _make_factory(int)
    key = DependencyKey(int, DEFAULT_COMPONENT)
    processed = {key: [first, second]}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)

    assert index.get(key) is second


def test_context_keys_includes_context_factory_at_root_scope():
    factory = _make_factory(bool, FactoryType.CONTEXT, Scope.APP)
    key = DependencyKey(bool, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)

    assert key in index.context_keys_at_root


def test_context_keys_excludes_context_factory_at_non_root_scope():
    factory = _make_factory(bool, FactoryType.CONTEXT, Scope.REQUEST)
    key = DependencyKey(bool, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)

    assert key not in index.context_keys_at_root


def test_context_keys_excludes_non_context_factory_at_root_scope():
    factory = _make_factory(int, FactoryType.FACTORY, Scope.APP)
    key = DependencyKey(int, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)

    assert key not in index.context_keys_at_root
