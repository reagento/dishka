from collections.abc import Callable
from functools import partial
from typing import TypeVar, overload

from dishka.entities.scope import BaseScope
from dishka.integrations.base import ProvideContext
from .injection import Injection

T = TypeVar("T")


class DishkaModule:
    """Declare injectable entry points independently of an application."""

    @overload
    def inject(self, func: Callable[..., T]) -> Callable[..., T]: ...

    @overload
    def inject(
        self,
        func: None = None,
        *,
        scope: BaseScope | None = None,
        provide_context: ProvideContext | None = None,
    ) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

    def inject(
        self,
        func: Callable[..., T] | None = None,
        *,
        scope: BaseScope | None = None,
        provide_context: ProvideContext | None = None,
    ) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
        """Inject marked parameters, opening a scope for the outermost call."""
        if func is None:
            return partial(
                self._inject, scope=scope, provide_context=provide_context,
            )
        return self._inject(func, scope, provide_context)

    def _inject(
        self,
        func: Callable[..., T],
        scope: BaseScope | None,
        provide_context: ProvideContext | None,
    ) -> Callable[..., T]:
        return Injection(self, func, scope, provide_context).wrap()
