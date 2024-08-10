from collections.abc import Sequence

from dishka.entities.key import DependencyKey
from .dependency_source import Factory

try:
    from builtins import ExceptionGroup  # type: ignore[attr-defined]

except ImportError:
    from exceptiongroup import (  # type: ignore[no-redef, import-not-found]
        ExceptionGroup,
    )

from .error_rendering import PathRenderer

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
    ) -> None:
        self.requested = requested
        self.path = list(path)

    def add_path(self, requested_by: Factory) -> None:
        self.path.insert(0, requested_by)

    def __str__(self) -> str:
        if self.path:
            return (
                f"Cannot find factory for {self.requested}. "
                f"It is missing or has invalid scope.\n"
            ) + _renderer.render(self.path, self.requested)
        else:
            return (
                f"Cannot find factory for {self.requested}. "
                f"Check scopes in your providers. "
                f"It is missing or has invalid scope."
            )


class GraphMissingFactoryError(NoFactoryError, InvalidGraphError):
    pass
