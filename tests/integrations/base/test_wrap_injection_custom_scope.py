from collections.abc import AsyncIterator, Callable, Iterator
from inspect import isasyncgenfunction, isgeneratorfunction

import pytest

from dishka import Container, Scope
from dishka.async_container import AsyncContainer
from dishka.entities.depends_marker import FromDishka
from dishka.integrations.base import wrap_injection
from tests.integrations.common import REQUEST_DEP_VALUE, StepDep


def generate_str(step: StepDep, prefix: int | None = None) -> str:
    s = str(step)
    if prefix is not None:
        s = f"{prefix}. {s}"
    return s


def sync_func(step: FromDishka[StepDep]) -> str:
    return generate_str(step)


def sync_gen(data: list[int], step: FromDishka[StepDep]) -> Iterator[str]:
    for i in data:
        yield generate_str(step, i)


async def async_func(step: FromDishka[StepDep]) -> str:
    return generate_str(step)


async def async_gen(
    data: list[int],
    step: FromDishka[StepDep],
) -> AsyncIterator[str]:
    for i in data:
        yield generate_str(step, i)


@pytest.mark.parametrize("func", [sync_func, sync_gen])
@pytest.mark.parametrize("manage_scope", [False, True])
def test_sync_custom_scope(
    func: Callable, manage_scope: bool, container: Container
) -> None:
    wrapped_func = wrap_injection(
        func=func,
        container_getter=lambda *_: container,
        is_async=False,
        manage_scope=manage_scope,
        scope=Scope.STEP,
    )

    if isgeneratorfunction(func):
        result = list(wrapped_func([1, 2]))
        assert result == [
            generate_str(StepDep(f"step for {REQUEST_DEP_VALUE}"), i)
            for i in [1, 2]
        ]
    else:
        result = wrapped_func()
        assert result == generate_str(StepDep(f"step for {REQUEST_DEP_VALUE}"))


@pytest.mark.asyncio
@pytest.mark.parametrize("func", [async_func, async_gen])
@pytest.mark.parametrize("manage_scope", [False, True])
async def test_async_custom_scope(
    func: Callable,
    manage_scope: bool,
    async_container: AsyncContainer,
) -> None:
    wrapped_func = wrap_injection(
        func=func,
        container_getter=lambda *_: async_container,
        is_async=True,
        manage_scope=manage_scope,
        scope=Scope.STEP,
    )

    if isasyncgenfunction(func):
        result = [item async for item in wrapped_func([1, 2])]
        assert result == [
            generate_str(StepDep(f"step for {REQUEST_DEP_VALUE}"), i)
            for i in [1, 2]
        ]
    else:
        result = await wrapped_func()
        assert result == generate_str(StepDep(f"step for {REQUEST_DEP_VALUE}"))
