from dishka.entities.factory_type import FactoryData, FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.scope import Scope
from dishka.text_rendering.suggestion import render_suggestions_for_missing


def test_suggest_abstract_factories() -> None:
    expected = (
        "\n * Try use `AnyOf` "
        "or changing the requested dependency to a more abstract. "
        "Found factories for more abstract dependencies: (object, int);"
    )
    suggest_abstract_factories = [
        FactoryData(
            source=int,
            provides=DependencyKey(object, ""),
            scope=Scope.APP,
            type_=FactoryType.FACTORY,
        ),
    ]

    result = render_suggestions_for_missing(
        requested_for=None,
        requested_key=DependencyKey(int, ""),
        suggest_other_scopes=[],
        suggest_other_components=[],
        suggest_abstract_factories=suggest_abstract_factories,
        suggest_concrete_factories=[],
    )

    assert result == expected


def test_suggest_concrete_factories() -> None:
    expected = (
        "\n * Try use `WithParents` "
        "or changing `provides` to `object`. "
        "Found factories for more concrete dependencies: (float, int);"
    )
    suggest_concrete_factories = [
        FactoryData(
            source=int,
            provides=DependencyKey(float, ""),
            scope=Scope.APP,
            type_=FactoryType.FACTORY,
        ),
    ]

    result = render_suggestions_for_missing(
        requested_for=None,
        requested_key=DependencyKey(object, ""),
        suggest_other_scopes=[],
        suggest_other_components=[],
        suggest_abstract_factories=[],
        suggest_concrete_factories=suggest_concrete_factories,
    )

    assert result == expected
