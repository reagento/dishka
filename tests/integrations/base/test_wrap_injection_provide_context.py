from collections.abc import AsyncIterator, Callable, Iterable, Iterator
from inspect import isasyncgenfunction, isgeneratorfunction

import pytest

from dishka.async_container import AsyncContainer
from dishka.container import Container
from dishka.entities.depends_marker import FromDishka
from dishka.integrations.base import wrap_injection
from dishka.integrations.exceptions import ImproperProvideContextUsageError
from tests.integrations.common import ContextDep


def sync_func(context: FromDishka[ContextDep]) -> str:
    return context


def sync_gen(
    data: Iterable[int],
    context: FromDishka[ContextDep],
) -> Iterator[str]:
    for i in data:
        yield f"{i}. {context}"


async def async_func(context: FromDishka[ContextDep]) -> str:
    return context


async def async_gen(
    data: Iterable[int],
    context: FromDishka[ContextDep],
) -> AsyncIterator[str]:
    for i in data:
        yield f"{i}. {context}"


@pytest.mark.parametrize("func", [sync_func, sync_gen])
def test_sync_provide_context(func: Callable, container: Container) -> None:
    wrapped_func = wrap_injection(
        func=func,
        container_getter=lambda *_: container,
        is_async=False,
        manage_scope=True,
        provide_context=lambda *_: {ContextDep: "context"},
    )

    if isgeneratorfunction(func):
        result = list(wrapped_func([1, 2]))
        assert result == ["1. context", "2. context"]
    else:
        result = wrapped_func()
        assert result == "context"


@pytest.mark.parametrize("func", [sync_func, sync_gen])
def test_invalid_provide_context(func: Callable, container: Container) -> None:
    with pytest.raises(ImproperProvideContextUsageError):
        wrap_injection(
            func=func,
            container_getter=lambda *_: container,
            is_async=False,
            manage_scope=False,
            provide_context=lambda *_: {ContextDep: "context"},
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("func", [async_func, async_gen])
async def test_async_provide_context(
    func: Callable,
    async_container: AsyncContainer,
) -> None:
    wrapped_func = wrap_injection(
        func=func,
        container_getter=lambda *_: async_container,
        is_async=True,
        manage_scope=True,
        provide_context=lambda *_: {ContextDep: "context"},
    )

    if isasyncgenfunction(func):
        result = [item async for item in wrapped_func([1, 2])]
        assert result == ["1. context", "2. context"]
    else:
        result = await wrapped_func()
        assert result == "context"


@pytest.mark.asyncio
@pytest.mark.parametrize("func", [async_func, async_gen])
async def test_invalid_async_provide_context(
    func: Callable,
    async_container: AsyncContainer,
) -> None:
    with pytest.raises(ImproperProvideContextUsageError):
        wrap_injection(
            func=func,
            container_getter=lambda *_: async_container,
            is_async=True,
            manage_scope=False,
            provide_context=lambda *_: {ContextDep: "context"},
        )
