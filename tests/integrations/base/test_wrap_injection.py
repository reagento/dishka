from collections.abc import Callable, Iterable, Iterator
from unittest.mock import Mock

import pytest

from dishka import AsyncContainer, FromDishka
from dishka.integrations.base import wrap_injection
from dishka.integrations.exceptions import InvalidInjectedFuncTypeError


def sync_func(mock: FromDishka[Mock]) -> None:
    mock.some_func()


def sync_gen(data: Iterable[int], x: FromDishka[Mock]) -> Iterator[int]:
    for i in data:
        yield x.some_func(i)


@pytest.mark.parametrize("func", [sync_func, sync_gen])
def test_invalid_injected_func_type(
    func: Callable,
    async_container: AsyncContainer,
) -> None:
    with pytest.raises(InvalidInjectedFuncTypeError):
        wrap_injection(
            func=func,
            container_getter=lambda *_: async_container,
            is_async=True,
        )
