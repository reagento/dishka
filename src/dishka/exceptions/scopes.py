from dishka.entities.scope import BaseScope
from dishka.exceptions.base import DishkaError


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
