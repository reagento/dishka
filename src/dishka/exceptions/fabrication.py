from collections.abc import Sequence
from typing import TYPE_CHECKING

from dishka._adaptix.common import TypeHint
from dishka.entities.factory_type import FactoryData
from dishka.exceptions.base import DishkaError
from dishka.text_rendering import get_name
from dishka.text_rendering.path import PathRenderer
from dishka.text_rendering.suggestion import render_suggestions_for_missing

if TYPE_CHECKING:
    from dishka import DependencyKey
    from dishka.dependency_source import Factory

_renderer = PathRenderer()


class UnsupportedFactoryError(DishkaError):
    pass


class NoFactoryError(DishkaError):
    def __init__(
            self,
            requested: "DependencyKey",
            path: Sequence["Factory"] = (),
            suggest_other_scopes: Sequence["Factory"] = (),
            suggest_other_components: Sequence["Factory"] = (),
    ) -> None:
        self.requested = requested
        self.path = list(path)
        self.suggest_other_scopes = suggest_other_scopes
        self.suggest_other_components = suggest_other_components

    def add_path(self, requested_by: "Factory") -> None:
        self.path.insert(0, requested_by)

    def __str__(self) -> str:
        requested_name = (
            f"({get_name(self.requested.type_hint, include_module=False)}, "
            f"component={self.requested.component!r})"
        )
        suggestion = render_suggestions_for_missing(
            requested_for=self.path[-1] if self.path else None,
            requested_key=self.requested,
            suggest_other_scopes=self.suggest_other_scopes,
            suggest_other_components=self.suggest_other_components,
        )
        if suggestion:
            suggestion = f"Hint:{suggestion}"
        if self.path:
            return (
                f"Cannot find factory for {requested_name}. "
                f"It is missing or has invalid scope.\n"
            ) + _renderer.render(self.path, self.requested) + suggestion
        else:
            return (
                f"Cannot find factory for {requested_name}. "
                f"Check scopes in your providers. "
                f"It is missing or has invalid scope."
            ) + suggestion


class NotAFactoryError(TypeError, DishkaError):
    def __init__(self, attempted_factory_type: type) -> None:
        self.type = attempted_factory_type

    def __str__(self) -> str:
        return f"Cannot use {self.type} as a factory"


class StartingClassIgnoredError(ValueError, DishkaError):
    def __init__(self, hint: TypeHint) -> None:
        self.hint = hint

    def __str__(self) -> str:
        return f"The starting class {self.hint!r} is in ignored types"


class AliasedFactoryNotFoundError(ValueError, DishkaError):
    def __init__(
            self, dependency: "DependencyKey", alias: FactoryData,
    ) -> None:
        self.dependency = dependency
        self.alias_provider = alias.provides

    def __str__(self) -> str:
        return (
            f"Factory for {self.dependency} "
            f"aliased from {self.alias_provider} is not found"
        )
