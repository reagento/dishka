from collections.abc import AsyncIterator, Callable, Iterable, Iterator
from inspect import isasyncgenfunction, isgeneratorfunction
from typing import Any, cast

import pytest

from dishka.async_container import AsyncContainer
from dishka.container import Container
from dishka.entities.depends_marker import FromDishka
from dishka.integrations.base import wrap_injection
from dishka.integrations.exceptions import ImproperProvideContextUsageError
from tests.integrations.common import ContextDep, UserDep

context = ContextDep("context")
user = UserDep(f"user_id.from_context({context})")


def generate_str(
    user: UserDep,
    context: ContextDep,
    prefix: int | None = None,
) -> str:
    s = f"{user}, context={context}"
    if prefix is not None:
        s = f"{prefix}. {s}"
    return s


def sync_func(
    context: ContextDep,
    user: FromDishka[UserDep],
) -> str:
    return generate_str(user, context)


def sync_gen(
    context: ContextDep,
    data: Iterable[int],
    user: FromDishka[UserDep],
) -> Iterator[str]:
    for i in data:
        yield generate_str(user, context, i)


async def async_func(
    context: ContextDep,
    user: FromDishka[UserDep],
) -> str:
    return generate_str(user, context)


async def async_gen(
    context: ContextDep,
    data: Iterable[int],
    user: FromDishka[UserDep],
) -> AsyncIterator[str]:
    for i in data:
        yield generate_str(user, context, i)


def provide_context(
    args: tuple[Any, ...],
    _: dict[str, Any],
) -> dict[Any, Any]:
    context = cast(ContextDep, args[0])
    return {ContextDep: context}


@pytest.mark.parametrize("func", [sync_func, sync_gen])
def test_sync_provide_context(func: Callable, container: Container) -> None:
    wrapped_func = wrap_injection(
        func=func,
        container_getter=lambda *_: container,
        is_async=False,
        manage_scope=True,
        provide_context=provide_context,
    )

    if isgeneratorfunction(func):
        result = list(wrapped_func(context, [1, 2]))
        assert result == [generate_str(user, context, i) for i in [1, 2]]
    else:
        result = wrapped_func(context)
        assert result == generate_str(user, context)


@pytest.mark.parametrize("func", [sync_func, sync_gen])
def test_invalid_provide_context(func: Callable, container: Container) -> None:
    with pytest.raises(ImproperProvideContextUsageError):
        wrap_injection(
            func=func,
            container_getter=lambda *_: container,
            is_async=False,
            manage_scope=False,
            provide_context=provide_context,
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
        provide_context=provide_context,
    )

    if isasyncgenfunction(func):
        result = [item async for item in wrapped_func(context, [1, 2])]
        assert result == [generate_str(user, context, i) for i in [1, 2]]
    else:
        result = await wrapped_func(context)
        assert result == generate_str(user, context)


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
            provide_context=provide_context,
        )
