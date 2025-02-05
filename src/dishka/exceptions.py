from collections.abc import Callable, Sequence
from typing import Any, TypeVar

from dishka import BaseScope
from dishka._adaptix.common import TypeHint
from dishka.entities.factory_type import FactoryData
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
    def __init__(
            self,
            scope: BaseScope | None,
            expected: type[BaseScope],
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


class NoChildScopesError(ValueError, DishkaError):
    def __str__(self) -> str:
        return "No child scopes found"


class NoNonSkippedScopesError(ValueError, DishkaError):
    def __str__(self) -> str:
        return "No non-skipped scopes found."


class ChildScopeNotFoundError(ValueError, DishkaError):
    def __init__(
            self,
            assumed_child_scope: BaseScope | None,
            current_scope: BaseScope | None,
    ) -> None:
        self.child_scope = assumed_child_scope
        self.current_scope = current_scope

    def __str__(self) -> str:
        return (
            f"Cannot find {self.child_scope} as a "
            f"child of current {self.current_scope}"
        )


class UnsupportedGeneratorReturnTypeError(TypeError, DishkaError):
    def __init__(
            self,
            name: str,
            guess: str,
            guessed_args: str,
            *,
            is_async: bool = False,
    ) -> None:
        self.name = name
        self.guess = guess
        self.guessed_args = guessed_args
        self.is_async = is_async

    def __str__(self) -> str:
        gen_type = "async generator" if self.is_async else "generator"
        return (
            f"Unsupported return type `{self.name}` for {gen_type}. "
            f"Did you mean {self.guess}[{self.guessed_args}]?"
        )


class MissingHintsError(ValueError, DishkaError):
    def __init__(
            self,
            source: Any,
            missing_hints: Sequence[str],
            *,
            append_init: bool = False,
    ) -> None:
        self.source = source
        self.missing = missing_hints
        self.append_init = append_init

    def __str__(self) -> str:
        name = get_name(self.source, include_module=True)
        if self.append_init:
            name += ".__init__"
        missing = ", ".join(self.missing)
        return (
            f"Failed to analyze `{name}`.\n"
            f"Some parameters do not have type hints: {missing}\n"
        )


class UndefinedTypeAnalysisError(NameError, DishkaError):
    def __init__(
            self,
            source: Any,
            type_name: str,
    ) -> None:
        self.source = source
        self.type_name = type_name
        self.message = self._construct_message()
        super().__init__(self.message, name=type_name)

    def _construct_message(self) -> str:
        name = get_name(self.source, include_module=True)
        return (
            f"Failed to analyze `{name}`. \n"
            f"Type '{self.type_name}' is not defined. \n\n"
            f"If your are using `if TYPE_CHECKING` "
            f"to import '{self.type_name}' "
            f"then try removing it. \n"
            f"Or, create a separate factory with all types imported."
        )

    def __str__(self) -> str:
        return self.message


class NoScopeSetInProvideError(ValueError, DishkaError):
    def __init__(
            self,
            provides_name: str,
            src_name: str,
            provider_name: str,
    ) -> None:
        self.provides_name = provides_name
        self.src_name = src_name
        self.provider_name = provider_name

    def __str__(self) -> str:
        return (
            f"No scope is set for {self.provides_name}.\n"
            f"Set in provide() call for {self.src_name} or "
            f"within {self.provider_name}"
        )


class NoScopeSetInContextError(ValueError, DishkaError):
    def __init__(
            self,
            provides_name: str,
            provider_name: str,
    ) -> None:
        self.provides_name = provides_name
        self.provider_name = provider_name

    def __str__(self) -> str:
        return (
            f"No scope is set for {self.provides_name}.\n"
            f"Set in from_context() call or within {self.provider_name}"
        )


class MissingReturnHintError(ValueError, DishkaError):
    def __init__(self, source: Any) -> None:
        self.source = source

    def __str__(self) -> str:
        name = get_name(self.source, include_module=True)
        return (
            f"Failed to analyze `{name}`. \n"
            f"Missing return type hint."
        )


class IndependentDecoratorError(ValueError, DishkaError):
    def __init__(self, source: Callable[..., Any] | type) -> None:
        self.source = source

    def __str__(self) -> str:
        name = get_name(self.source, include_module=True)
        return (
            f"Decorator {name} does not depends on provided type.\n"
            f"Did you mean @provide instead of @decorate?"
        )


class NotAFactoryError(TypeError, DishkaError):
    def __init__(self, attempted_factory_type: type) -> None:
        self.type = attempted_factory_type

    def __str__(self) -> str:
        return f"Cannot use {self.type} as a factory"


class UnsupportedGenericBoundsError(TypeError, DishkaError):
    def __init__(self, bounds: TypeVar) -> None:
        self.bounds = bounds

    def __str__(self) -> str:
        return f"Generic bounds are not supported: {self.bounds}"


class StartingClassIgnoredError(ValueError, DishkaError):
    def __init__(self, hint: TypeHint) -> None:
        self.hint = hint

    def __str__(self) -> str:
        return f"The starting class {self.hint!r} is in ignored types"


class AliasedFactoryNotFoundError(ValueError, DishkaError):
    def __init__(
            self, dependency: DependencyKey, alias: FactoryData,
    ) -> None:
        self.dependency = dependency
        self.alias_provider = alias.provides

    def __str__(self) -> str:
        return (
            f"Factory for {self.dependency} "
            f"aliased from {self.alias_provider} is not found"
        )
