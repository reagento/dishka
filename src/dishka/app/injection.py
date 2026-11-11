from collections.abc import AsyncGenerator, AsyncIterator, Callable, Generator
from contextlib import asynccontextmanager
from functools import wraps
from inspect import (
    isasyncgenfunction,
    iscoroutinefunction,
    isgeneratorfunction,
)
from types import TracebackType
from typing import Any, get_type_hints, overload

from dishka.async_container import AsyncContainer
from dishka.entities.scope import BaseScope
from dishka.integrations.base import ProvideContext, wrap_injection
from dishka.integrations.exceptions import InvalidInjectedFuncTypeError
from .context import (
    AppContext,
    CallScope,
    activate_scope,
    get_app,
    get_async_container,
    get_sync_container,
)


class Injection:
    def __init__(
        self,
        module: object,
        func: Callable[..., Any],
        scope: BaseScope | None,
        provide_context: ProvideContext | None,
    ) -> None:
        self.module = module
        self.func = func
        self.scope = scope
        self.provide_context = provide_context
        self.async_func = (
            iscoroutinefunction(func) or isasyncgenfunction(func)
        )
        if isasyncgenfunction(func):
            injection_target = _make_async_generator_factory(func)
        elif isgeneratorfunction(func):
            injection_target = _make_generator_factory(func)
        else:
            injection_target = func
        self.sync_injected = wrap_injection(
            func=injection_target, container_getter=get_sync_container,
        )
        self.async_injected = (
            wrap_injection(
                func=injection_target,
                container_getter=get_async_container,
                is_async=True,
            )
            if self.async_func else self.sync_injected
        )

    def get_call(
        self, args: tuple[Any, ...], kwargs: dict[str, Any],
    ) -> tuple[AppContext, Callable[..., Any], dict[Any, Any] | None]:
        app = get_app(self.module)
        if isinstance(app.container, AsyncContainer):
            if not self.async_func:
                raise InvalidInjectedFuncTypeError(self.func.__name__)
            injected = self.async_injected
        else:
            injected = self.sync_injected
        context = (
            self.provide_context(args, kwargs)
            if self.provide_context else None
        )
        return app, injected, context

    def wrap(self) -> Callable[..., Any]:
        if isasyncgenfunction(self.func):
            return self._make_async_generator_wrapper()
        if isgeneratorfunction(self.func):
            return self._make_generator_wrapper()
        if iscoroutinefunction(self.func):
            return self._make_async_wrapper()
        return self._make_sync_wrapper()

    def _make_sync_wrapper(self) -> Callable[..., Any]:
        @wraps(self.sync_injected)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._call_sync(args, kwargs)

        return wrapper

    def _make_async_wrapper(self) -> Callable[..., Any]:
        @wraps(self.sync_injected)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await self._call_async(args, kwargs)

        return wrapper

    def _make_generator_wrapper(self) -> Callable[..., Any]:
        @wraps(self.sync_injected)
        def wrapper(*args: Any, **kwargs: Any) -> Generator[Any, Any, Any]:
            return (yield from self._iterate_sync(args, kwargs))

        return wrapper

    def _make_async_generator_wrapper(self) -> Callable[..., Any]:
        @wraps(self.sync_injected)
        async def wrapper(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            async with self._async_iterator(args, kwargs) as iterator:
                value = None
                error: BaseException | None = None
                while True:
                    try:
                        item = (
                            await iterator.asend(value) if error is None
                            else await iterator.athrow(error)
                        )
                    except StopAsyncIteration:
                        break
                    # Capture exceptions injected by athrow without swallowing
                    # them: the next iteration forwards them to the producer.
                    with iterator.capture_throw():
                        value = yield item
                    error = iterator.error

        return wrapper

    def _call_sync(
        self, args: tuple[Any, ...], kwargs: dict[str, Any],
    ) -> Any:
        app, injected, context = self.get_call(args, kwargs)
        manager = app.sync_scope(self.scope, context)
        with manager as state, activate_scope(state):
            return injected(*args, **kwargs)

    async def _call_async(
        self, args: tuple[Any, ...], kwargs: dict[str, Any],
    ) -> Any:
        app, injected, context = self.get_call(args, kwargs)
        async with app.async_scope(self.scope, context) as state:
            with activate_scope(state):
                return await injected(*args, **kwargs)

    def _iterate_sync(
        self, args: tuple[Any, ...], kwargs: dict[str, Any],
    ) -> Generator[Any, Any, Any]:
        app, injected, context = self.get_call(args, kwargs)
        with app.sync_scope(self.scope, context) as state:
            with activate_scope(state):
                iterator = injected(*args, **kwargs)
            return (yield from _ScopedGenerator(iterator, state))

    @asynccontextmanager
    async def _async_iterator(
        self, args: tuple[Any, ...], kwargs: dict[str, Any],
    ) -> AsyncIterator["_ScopedAsyncGenerator"]:
        app, injected, context = self.get_call(args, kwargs)
        async with app.async_scope(self.scope, context) as state:
            with activate_scope(state):
                iterator = await injected(*args, **kwargs)
            try:
                yield _ScopedAsyncGenerator(iterator, state)
            finally:
                with activate_scope(state):
                    await iterator.aclose()


def _make_generator_factory(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def factory(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    factory.__annotations__ = get_type_hints(func, include_extras=True)
    return factory


def _make_async_generator_factory(
    func: Callable[..., Any],
) -> Callable[..., Any]:
    @wraps(func)
    async def factory(*args: Any, **kwargs: Any) -> Any:
        return func(*args, **kwargs)

    factory.__annotations__ = get_type_hints(func, include_extras=True)
    return factory


class _ScopedAsyncGenerator:
    """Activate the scope only while the async generator is executing."""

    def __init__(
        self, iterator: AsyncGenerator[Any, Any], state: CallScope,
    ) -> None:
        self.iterator = iterator
        self.state = state
        self.error: BaseException | None = None

    async def asend(self, value: Any) -> Any:
        with activate_scope(self.state):
            return await self.iterator.asend(value)

    async def athrow(self, error: BaseException) -> Any:
        with activate_scope(self.state):
            return await self.iterator.athrow(error)

    def capture_throw(self) -> "_ScopedAsyncGenerator":
        self.error = None
        return self

    def __enter__(self) -> None:
        pass

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self.error = exc_value
        return (
            exc_value is not None
            and not isinstance(exc_value, GeneratorExit)
        )


class _ScopedGenerator(Generator[Any, Any, Any]):
    """Activate the scope only while the generator is executing."""

    def __init__(
        self, iterator: Generator[Any, Any, Any], state: CallScope,
    ) -> None:
        self.iterator = iterator
        self.state = state

    def send(self, value: Any) -> Any:
        with activate_scope(self.state):
            return self.iterator.send(value)

    @overload
    def throw(
        self,
        typ: type[BaseException],
        val: object = None,
        tb: TracebackType | None = None,
        /,
    ) -> Any: ...

    @overload
    def throw(
        self,
        typ: BaseException,
        val: None = None,
        tb: TracebackType | None = None,
        /,
    ) -> Any: ...

    def throw(
        self,
        typ: type[BaseException] | BaseException,
        val: Any = None,
        tb: TracebackType | None = None,
        /,
    ) -> Any:
        with activate_scope(self.state):
            if val is None and tb is None:
                return self.iterator.throw(typ)
            if isinstance(typ, BaseException):
                return self.iterator.throw(typ, val, tb)
            return self.iterator.throw(typ, val, tb)

    def close(self) -> None:
        with activate_scope(self.state):
            self.iterator.close()
