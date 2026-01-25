from dishka import Marker, Scope
from dishka.dependency_source.factory import Factory
from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.marker import (
    AndMarker,
    BaseMarker,
    BoolMarker,
    NotMarker,
    OrMarker,
)
from dishka.processed_factory_filter import ProcessedFactoryFilter


def _make_factory(
    type_hint: type,
    when_active: BaseMarker | None = None,
    component: str = DEFAULT_COMPONENT,
) -> Factory:
    return Factory(
        dependencies=[],
        kw_dependencies={},
        source=lambda: None,
        provides=DependencyKey(type_hint, component),
        scope=Scope.APP,
        type_=FactoryType.FACTORY,
        is_to_bind=False,
        cache=True,
        when_override=None,
        when_active=when_active,
        when_component=None,
        when_dependencies={},
    )


def _make_activation_results(
    marker: Marker,
    *,
    value: bool,
    component: str = DEFAULT_COMPONENT,
) -> dict[DependencyKey, bool]:
    return {DependencyKey(marker, component): value}


def test_keeps_factory_when_marker_active():
    marker = Marker("Feature")
    factory = _make_factory(str, when_active=marker)
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = _make_activation_results(marker, value=True)

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert len(result[key]) == 1
    assert result[key][0] is factory


def test_removes_factory_when_marker_inactive():
    marker = Marker("Feature")
    factory = _make_factory(str, when_active=marker)
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = _make_activation_results(marker, value=False)

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert key not in result


def test_keeps_factory_when_marker_not_in_results():
    marker = Marker("Unknown")
    factory = _make_factory(str, when_active=marker)
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    result = ProcessedFactoryFilter({}).filter(processed)

    assert len(result[key]) == 1


def test_keeps_factory_without_when_active():
    factory = _make_factory(str, when_active=None)
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    result = ProcessedFactoryFilter({}).filter(processed)

    assert len(result[key]) == 1
    assert result[key][0] is factory


def test_not_marker_removes_when_inner_active():
    inner = Marker("Feature")
    factory = _make_factory(str, when_active=NotMarker(inner))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = _make_activation_results(inner, value=True)

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert key not in result


def test_not_marker_keeps_when_inner_inactive():
    inner = Marker("Feature")
    factory = _make_factory(str, when_active=NotMarker(inner))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = _make_activation_results(inner, value=False)

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert len(result[key]) == 1


def test_not_marker_keeps_when_inner_unknown():
    inner = Marker("Unknown")
    factory = _make_factory(str, when_active=NotMarker(inner))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    result = ProcessedFactoryFilter({}).filter(processed)

    assert len(result[key]) == 1


def test_or_marker_keeps_when_left_active():
    left = Marker("A")
    right = Marker("B")
    factory = _make_factory(str, when_active=OrMarker(left, right))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = {
        DependencyKey(left, DEFAULT_COMPONENT): True,
        DependencyKey(right, DEFAULT_COMPONENT): False,
    }

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert len(result[key]) == 1


def test_or_marker_keeps_when_right_active():
    left = Marker("A")
    right = Marker("B")
    factory = _make_factory(str, when_active=OrMarker(left, right))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = {
        DependencyKey(left, DEFAULT_COMPONENT): False,
        DependencyKey(right, DEFAULT_COMPONENT): True,
    }

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert len(result[key]) == 1


def test_or_marker_removes_when_both_inactive():
    left = Marker("A")
    right = Marker("B")
    factory = _make_factory(str, when_active=OrMarker(left, right))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = {
        DependencyKey(left, DEFAULT_COMPONENT): False,
        DependencyKey(right, DEFAULT_COMPONENT): False,
    }

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert key not in result


def test_or_marker_keeps_when_one_side_unknown():
    left = Marker("A")
    right = Marker("Unknown")
    factory = _make_factory(str, when_active=OrMarker(left, right))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = {
        DependencyKey(left, DEFAULT_COMPONENT): False,
    }

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert len(result[key]) == 1


def test_and_marker_keeps_when_both_active():
    left = Marker("A")
    right = Marker("B")
    factory = _make_factory(str, when_active=AndMarker(left, right))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = {
        DependencyKey(left, DEFAULT_COMPONENT): True,
        DependencyKey(right, DEFAULT_COMPONENT): True,
    }

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert len(result[key]) == 1


def test_and_marker_removes_when_left_inactive():
    left = Marker("A")
    right = Marker("B")
    factory = _make_factory(str, when_active=AndMarker(left, right))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = {
        DependencyKey(left, DEFAULT_COMPONENT): False,
        DependencyKey(right, DEFAULT_COMPONENT): True,
    }

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert key not in result


def test_and_marker_removes_when_right_inactive():
    left = Marker("A")
    right = Marker("B")
    factory = _make_factory(str, when_active=AndMarker(left, right))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = {
        DependencyKey(left, DEFAULT_COMPONENT): True,
        DependencyKey(right, DEFAULT_COMPONENT): False,
    }

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert key not in result


def test_and_marker_keeps_when_one_side_unknown():
    left = Marker("A")
    right = Marker("Unknown")
    factory = _make_factory(str, when_active=AndMarker(left, right))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = {
        DependencyKey(left, DEFAULT_COMPONENT): True,
    }

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert len(result[key]) == 1


def test_bool_marker_true_keeps_factory():
    factory = _make_factory(str, when_active=BoolMarker(True))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    result = ProcessedFactoryFilter({}).filter(processed)

    assert len(result[key]) == 1


def test_bool_marker_false_keeps_factory():
    factory = _make_factory(str, when_active=BoolMarker(False))
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    result = ProcessedFactoryFilter({}).filter(processed)

    assert len(result[key]) == 1


def test_returns_original_when_empty_activation_results():
    factory = _make_factory(str)
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}

    result = ProcessedFactoryFilter({}).filter(processed)

    assert result is processed


def test_filters_multiple_factories_for_same_key():
    marker = Marker("Feature")
    default_factory = _make_factory(str, when_active=None)
    feature_factory = _make_factory(str, when_active=marker)
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [default_factory, feature_factory]}
    activation_results = _make_activation_results(marker, value=False)

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert len(result[key]) == 1
    assert result[key][0] is default_factory


def test_removes_key_when_all_factories_filtered():
    marker = Marker("Feature")
    factory = _make_factory(str, when_active=marker)
    key = DependencyKey(str, DEFAULT_COMPONENT)
    processed = {key: [factory]}
    activation_results = _make_activation_results(marker, value=False)

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert key not in result


def test_handles_custom_component():
    marker = Marker("Feature")
    custom_component = "custom"
    factory = _make_factory(
        str, when_active=marker, component=custom_component,
    )
    key = DependencyKey(str, custom_component)
    processed = {key: [factory]}
    activation_results = _make_activation_results(
        marker, value=True, component=custom_component,
    )

    result = ProcessedFactoryFilter(activation_results).filter(processed)

    assert len(result[key]) == 1
