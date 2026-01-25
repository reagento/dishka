from dishka import Scope
from dishka.activator_classifier import (
    ActivatorClassifier,
    ActivatorType,
)
from dishka.dependency_source.activator import Activator
from dishka.dependency_source.factory import Factory
from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.marker import Marker
from dishka.factory_index import FactoryIndex


def _make_factory(
    type_hint: type,
    factory_type: FactoryType = FactoryType.FACTORY,
    scope: Scope = Scope.APP,
    component: str = DEFAULT_COMPONENT,
    dependencies: list[DependencyKey] | None = None,
    kw_dependencies: dict[str, DependencyKey] | None = None,
) -> Factory:
    return Factory(
        dependencies=dependencies or [],
        kw_dependencies=kw_dependencies or {},
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


def _make_activator(
    marker_type: type[Marker],
    factory_type: FactoryType = FactoryType.FACTORY,
    dependencies: list[DependencyKey] | None = None,
    kw_dependencies: dict[str, DependencyKey] | None = None,
) -> Activator:
    factory = Factory(
        dependencies=dependencies or [],
        kw_dependencies=kw_dependencies or {},
        source=lambda: True,
        provides=DependencyKey(bool, DEFAULT_COMPONENT),
        scope=Scope.APP,
        type_=factory_type,
        is_to_bind=False,
        cache=True,
        when_override=None,
        when_active=None,
        when_component=None,
        when_dependencies={},
    )
    return Activator(
        factory=factory,
        marker=None,
        marker_type=marker_type,
    )


class MarkerA(Marker):
    pass


class MarkerB(Marker):
    pass


class MarkerC(Marker):
    pass


def test_classify_async_factory_as_dynamic():
    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA, FactoryType.ASYNC_FACTORY)
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].type == ActivatorType.DYNAMIC


def test_classify_async_generator_as_dynamic():
    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA, FactoryType.ASYNC_GENERATOR)
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].type == ActivatorType.DYNAMIC


def test_classify_sync_generator_based_on_deps():
    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA, FactoryType.GENERATOR)
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].type == ActivatorType.STATIC


def test_classify_with_root_context_dep_as_static():
    bool_key = DependencyKey(bool, DEFAULT_COMPONENT)
    context_factory = _make_factory(bool, FactoryType.CONTEXT, Scope.APP)
    processed = {bool_key: [context_factory]}

    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA, dependencies=[bool_key])
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].type == ActivatorType.STATIC


def test_classify_with_registered_non_context_dep_as_dynamic():
    int_key = DependencyKey(int, DEFAULT_COMPONENT)
    regular_factory = _make_factory(int, FactoryType.FACTORY, Scope.APP)
    processed = {int_key: [regular_factory]}

    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA, dependencies=[int_key])
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].type == ActivatorType.DYNAMIC


def test_classify_with_unregistered_dep_as_static():
    str_key = DependencyKey(str, DEFAULT_COMPONENT)

    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA, dependencies=[str_key])
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].type == ActivatorType.STATIC


def test_classify_with_kw_dep_root_context_as_static():
    bool_key = DependencyKey(bool, DEFAULT_COMPONENT)
    context_factory = _make_factory(bool, FactoryType.CONTEXT, Scope.APP)
    processed = {bool_key: [context_factory]}

    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(
        MarkerA,
        kw_dependencies={"flag": bool_key},
    )
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].type == ActivatorType.STATIC


def test_classify_empty_activators_returns_empty():
    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, {}, Scope.APP)

    result = classifier.classify()

    assert result == {}


def test_classify_multiple_independent_activators():
    marker_a_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    marker_b_key = DependencyKey(MarkerB, DEFAULT_COMPONENT)
    activator_a = _make_activator(MarkerA)
    activator_b = _make_activator(MarkerB)
    activators = {marker_a_key: activator_a, marker_b_key: activator_b}

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert len(result) == 2
    assert result[marker_a_key].type == ActivatorType.STATIC
    assert result[marker_b_key].type == ActivatorType.STATIC


def test_classify_activator_depending_on_static_activator():
    marker_a_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    marker_b_key = DependencyKey(MarkerB, DEFAULT_COMPONENT)
    activator_a = _make_activator(MarkerA)
    activator_b = _make_activator(MarkerB, dependencies=[marker_a_key])
    activators = {marker_a_key: activator_a, marker_b_key: activator_b}

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_a_key].type == ActivatorType.STATIC
    assert result[marker_b_key].type == ActivatorType.STATIC


def test_classify_activator_depending_on_dynamic_activator():
    marker_a_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    marker_b_key = DependencyKey(MarkerB, DEFAULT_COMPONENT)
    activator_a = _make_activator(MarkerA, FactoryType.ASYNC_FACTORY)
    activator_b = _make_activator(MarkerB, dependencies=[marker_a_key])
    activators = {marker_a_key: activator_a, marker_b_key: activator_b}

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_a_key].type == ActivatorType.DYNAMIC
    assert result[marker_b_key].type == ActivatorType.DYNAMIC


def test_classify_transitive_dynamic_propagation():
    marker_a_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    marker_b_key = DependencyKey(MarkerB, DEFAULT_COMPONENT)
    marker_c_key = DependencyKey(MarkerC, DEFAULT_COMPONENT)
    activator_a = _make_activator(MarkerA, FactoryType.ASYNC_FACTORY)
    activator_b = _make_activator(MarkerB, dependencies=[marker_a_key])
    activator_c = _make_activator(MarkerC, dependencies=[marker_b_key])
    activators = {
        marker_a_key: activator_a,
        marker_b_key: activator_b,
        marker_c_key: activator_c,
    }

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_a_key].type == ActivatorType.DYNAMIC
    assert result[marker_b_key].type == ActivatorType.DYNAMIC
    assert result[marker_c_key].type == ActivatorType.DYNAMIC


def test_classify_marker_dependency_excluded_from_deps():
    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    marker_dep_key = DependencyKey(Marker, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA, dependencies=[marker_dep_key])
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].dependencies == frozenset()


def test_classify_own_marker_type_excluded_from_deps():
    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    own_marker_dep = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA, dependencies=[own_marker_dep])
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].type == ActivatorType.STATIC


def test_classified_activator_contains_correct_data():
    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA)
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories({}, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    classified = result[marker_key]
    assert classified.key == marker_key
    assert classified.activator is activator
    assert classified.type == ActivatorType.STATIC
    assert classified.dependencies == frozenset()


def test_classify_non_root_context_dep_as_dynamic():
    bool_key = DependencyKey(bool, DEFAULT_COMPONENT)
    context_factory = _make_factory(bool, FactoryType.CONTEXT, Scope.REQUEST)
    processed = {bool_key: [context_factory]}

    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA, dependencies=[bool_key])
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].type == ActivatorType.DYNAMIC


def test_classify_mixed_deps_root_context_and_registered_as_dynamic():
    bool_key = DependencyKey(bool, DEFAULT_COMPONENT)
    int_key = DependencyKey(int, DEFAULT_COMPONENT)
    context_factory = _make_factory(bool, FactoryType.CONTEXT, Scope.APP)
    regular_factory = _make_factory(int, FactoryType.FACTORY, Scope.APP)
    processed = {bool_key: [context_factory], int_key: [regular_factory]}

    marker_key = DependencyKey(MarkerA, DEFAULT_COMPONENT)
    activator = _make_activator(MarkerA, dependencies=[bool_key, int_key])
    activators = {marker_key: activator}

    index = FactoryIndex.from_processed_factories(processed, Scope.APP)
    classifier = ActivatorClassifier(index, activators, Scope.APP)

    result = classifier.classify()

    assert result[marker_key].type == ActivatorType.DYNAMIC
