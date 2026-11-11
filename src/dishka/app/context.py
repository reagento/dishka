from asyncio import Lock as AsyncLock
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from threading import Lock
from typing import Any, cast

from dishka.async_container import AsyncContainer
from dishka.container import Container
from dishka.entities.scope import BaseScope
from .exceptions import (
    ActiveAppScopesError,
    AppAlreadyEnteredError,
    AppScopeClosedError,
    ModuleNotIncludedError,
    NoActiveAppError,
)

_active_app: ContextVar["AppContext"] = ContextVar("dishka_active_app")


@dataclass
class CallScope:
    app: "AppContext"
    container: Container | AsyncContainer
    active: bool = True


_call_scope: ContextVar[CallScope] = ContextVar("dishka_call_scope")


def get_app(module: object) -> "AppContext":
    app = _active_app.get(None)
    if app is None or not app.active:
        raise NoActiveAppError
    if module not in app.modules:
        raise ModuleNotIncludedError
    return app


def get_sync_container(
    args: tuple[Any, ...], kwargs: dict[str, Any],
) -> Container:
    return cast(Container, _call_scope.get().container)


def get_async_container(
    args: tuple[Any, ...], kwargs: dict[str, Any],
) -> AsyncContainer:
    return cast(AsyncContainer, _call_scope.get().container)


@contextmanager
def activate_scope(state: CallScope) -> Iterator[None]:
    if not state.active:
        raise AppScopeClosedError
    token = _call_scope.set(state)
    try:
        yield
    finally:
        _call_scope.reset(token)


class AppContext:
    """Internal runtime shared by application lifecycle and injection."""

    def __init__(self, container: Container | AsyncContainer) -> None:
        self.container = container
        self.modules: set[object] = set()
        self.active = False
        self._token: Token[AppContext] | None = None
        self._entered = False
        self._call_scopes: set[int] = set()
        self._closing = False
        self._closed = False
        self._exit_exception: BaseException | None = None

    def enter(self) -> None:
        if self._entered:
            raise AppAlreadyEnteredError
        self._token = _active_app.set(self)
        self._entered = True
        self.active = True

    def start_exit(self, exception: BaseException | None) -> None:
        if self._token is None or not self.active:
            raise NoActiveAppError
        _active_app.reset(self._token)
        self._token = None
        self.active = False
        self._exit_exception = exception
        self._closing = True
        if self._call_scopes:
            raise ActiveAppScopesError(len(self._call_scopes))

    def close_sync(self) -> None:
        if self._closed:
            return
        self._closed = True
        cast(Container, self.container).close(self._exit_exception)

    async def close_async(self) -> None:
        if self._closed:
            return
        self._closed = True
        if isinstance(self.container, AsyncContainer):
            await self.container.close(self._exit_exception)
        else:
            self.container.close(self._exit_exception)

    def _parent_scope(self) -> CallScope | None:
        state = _call_scope.get(None)
        if state is not None and state.app is self:
            if not state.active:
                raise AppScopeClosedError
            return state
        return None

    @contextmanager
    def sync_scope(
        self, scope: BaseScope | None, context: dict[Any, Any] | None,
    ) -> Iterator[CallScope]:
        parent = self._parent_scope()
        if parent is not None and scope is None and context is None:
            yield parent
            return
        container = parent.container if parent else self.container
        manager = cast(Container, container)(
            context, lock_factory=Lock, scope=scope,
        )
        state: CallScope | None = None
        try:
            with manager as child:
                state = CallScope(self, child)
                self._call_scopes.add(id(state))
                try:
                    yield state
                finally:
                    state.active = False
        finally:
            if state is not None:
                self._call_scopes.remove(id(state))
            if self._closing and not self._call_scopes:
                self.close_sync()

    @asynccontextmanager
    async def async_scope(
        self, scope: BaseScope | None, context: dict[Any, Any] | None,
    ) -> AsyncIterator[CallScope]:
        if isinstance(self.container, Container):
            with self.sync_scope(scope, context) as sync_state:
                yield sync_state
            return
        parent = self._parent_scope()
        if parent is not None and scope is None and context is None:
            yield parent
            return
        container = parent.container if parent else self.container
        manager = cast(AsyncContainer, container)(
            context, lock_factory=AsyncLock, scope=scope,
        )
        state: CallScope | None = None
        try:
            async with manager as child:
                state = CallScope(self, child)
                self._call_scopes.add(id(state))
                try:
                    yield state
                finally:
                    state.active = False
        finally:
            if state is not None:
                self._call_scopes.remove(id(state))
            if self._closing and not self._call_scopes:
                await self.close_async()
