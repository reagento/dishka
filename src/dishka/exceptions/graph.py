from collections.abc import Sequence
from typing import TYPE_CHECKING

from dishka.dependency_source import Factory
from dishka.exceptions.base import DishkaError
from dishka.exceptions.fabrication import NoFactoryError
from dishka.text_rendering import get_name
from dishka.text_rendering.path import PathRenderer

if TYPE_CHECKING:
    from dishka import BaseScope

_renderer = PathRenderer()


class InvalidGraphError(DishkaError):
    pass


class UnknownScopeError(InvalidGraphError):
    def __init__(
            self,
            scope: "BaseScope | None",
            expected: type["BaseScope"],
            extend_message: str = "",
    ) -> None:
        self.scope = scope
        self.expected = expected
        self.extend_message = extend_message

    def __str__(self) -> str:
        return " ".join((
            f"Scope {self.scope} is unknown, "
            f"expected one of {self.expected}",
            self.extend_message,
        ))


class CycleDependenciesError(InvalidGraphError):
    def __init__(self, path: Sequence["Factory"]) -> None:
        self.path = path

    def __str__(self) -> str:
        if len(self.path) == 1:
            hint = " Did you mean @decorate instead of @provide?"
        else:
            hint = ""
        details = _renderer.render(self.path)
        return f"Cycle dependencies detected.{hint}\n{details}"


class GraphMissingFactoryError(NoFactoryError, InvalidGraphError):
    pass


class ImplicitOverrideDetectedError(InvalidGraphError):
    def __init__(self, new: "Factory", existing: "Factory") -> None:
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
    def __init__(self, factory: "Factory") -> None:
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
