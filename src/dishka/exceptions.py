from collections.abc import Sequence

from dishka.entities.key import DependencyKey
from .dependency_source import Factory
from .text_rendering import get_name
from .text_rendering.suggestion import render_suggestions_for_missing

try:
    from builtins import ExceptionGroup  # type: ignore[attr-defined]

except ImportError:
    from exceptiongroup import (  # type: ignore[no-redef, import-not-found]
        ExceptionGroup,
    )

from .text_rendering.path import PathRenderer

_renderer = PathRenderer()


class DishkaError(Exception):
    pass


class InvalidGraphError(DishkaError):
    pass


class UnknownScopeError(InvalidGraphError):
    pass


class CycleDependenciesError(InvalidGraphError):
    def __init__(self, path: Sequence[Factory]) -> None:
        self.path = path

    def __str__(self) -> str:
        if len(self.path) == 1:
            hint = " Did you mean @decorate instead of @provide?"
        else:
            hint = ""
        details = _renderer.render(self.path)
        return f"Cycle dependencies detected.{hint}\n{details}"


class ExitError(ExceptionGroup[Exception], DishkaError):
    pass


class UnsupportedFactoryError(DishkaError):
    pass


class NoContextValueError(DishkaError):
    pass


class NoFactoryError(DishkaError):
    def __init__(
            self,
            requested: DependencyKey,
            path: Sequence[Factory] = (),
            suggest_other_scopes: Sequence[Factory] = (),
            suggest_other_components: Sequence[Factory] = (),
    ) -> None:
        self.requested = requested
        self.path = list(path)
        self.suggest_other_scopes = suggest_other_scopes
        self.suggest_other_components = suggest_other_components

    def add_path(self, requested_by: Factory) -> None:
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


class GraphMissingFactoryError(NoFactoryError, InvalidGraphError):
    pass


class ImplicitOverrideDetectedError(InvalidGraphError):
    def __init__(self, new: Factory, existing: Factory) -> None:
        self.new = new
        self.existing = existing

    def __str__(self) -> str:
        new_name = get_name(self.new.source, include_module=False)
        existing_name = get_name(self.existing.source, include_module=False)
        return (
            f"Detected multiple factories for {self.new.provides} "
            f"while `override` flag is not set.\n"
            "Hint:\n"
            f" * Try specifying `override=True` for {new_name}\n"
            f" * Try removing factory {existing_name} or {new_name}\n"
        )


class NothingOverriddenError(InvalidGraphError):
    def __init__(self, factory: Factory) -> None:
        self.factory = factory

    def __str__(self) -> str:
        name = get_name(self.factory.source, include_module=False)
        return (
            f"Overriding factory found for {self.factory.provides}, "
            "but there is nothing to override.\n"
            "Hint:\n"
            f" * Try removing override=True from {name}\n"
            f" * Check the order of providers\n"
        )

