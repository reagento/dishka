from collections.abc import AsyncIterator, Callable, Iterator
from inspect import Parameter
from typing import Final
from unittest.mock import Mock

import pytest

from dishka import AsyncContainer, Container, FromDishka
from dishka.integrations.base import wrap_injection
from dishka.integrations.exceptions import InvalidInjectedFuncTypeError
from tests.integrations.common import AppProvider

_CONTAINER_PARAM: Final = Parameter(
    name="dishka_container",
    annotation=Container,
    kind=Parameter.KEYWORD_ONLY,
)


def sync_func(mock: FromDishka[Mock]) -> None:
    mock()


def sync_gen(mock: FromDishka[Mock]) -> Iterator[None]:
    mock()
    yield


async def async_func(mock: FromDishka[Mock]) -> None:
    mock()


async def async_gen(
    mock: FromDishka[Mock],
) -> AsyncIterator[None]:
    mock()
    yield





@pytest.mark.parametrize("func", [sync_func, sync_gen])
def test_invalid_injected_func_type(
    func: Callable,
    async_container: AsyncContainer,
) -> None:
    with pytest.raises(InvalidInjectedFuncTypeError, match=func.__name__):
        wrap_injection(
            func=func,
            container_getter=lambda *_: async_container,
            is_async=True,
        )


def test_sync_func_container_getter_with_additional_param(
    container: Container,
    app_provider: AppProvider,
) -> None:
    mock = app_provider.mock

    wrapped_func = wrap_injection(
        func=sync_func,
        container_getter=lambda args, kwargs: kwargs[_CONTAINER_PARAM.name],
        additional_params=[_CONTAINER_PARAM],
        manage_scope=True,
        is_async=False,
    )
    wrapped_func(**{_CONTAINER_PARAM.name: container})

    mock.assert_called_once()


def test_sync_gen_container_getter_with_additional_param(
    container: Container,
    app_provider: AppProvider,
) -> None:
    mock = app_provider.mock

    wrapped_func = wrap_injection(
        func=sync_gen,
        container_getter=lambda args, kwargs: kwargs[_CONTAINER_PARAM.name],
        additional_params=[_CONTAINER_PARAM],
        manage_scope=True,
        is_async=False,
    )
    next(iter(wrapped_func(**{_CONTAINER_PARAM.name: container})))

    mock.assert_called_once()


@pytest.mark.asyncio
async def test_async_func_container_getter_with_additional_param(
    container: Container,
    app_provider: AppProvider,
) -> None:
    mock = app_provider.mock

    wrapped_func = wrap_injection(
        func=async_func,
        container_getter=lambda args, kwargs: kwargs[_CONTAINER_PARAM.name],
        additional_params=[_CONTAINER_PARAM],
        manage_scope=True,
        is_async=False,
    )
    await wrapped_func(**{_CONTAINER_PARAM.name: container})

    mock.assert_called_once()


@pytest.mark.asyncio
async def test_async_gen_container_getter_with_additional_param(
    container: Container,
    app_provider: AppProvider,
) -> None:
    mock = app_provider.mock

    wrapped_func = wrap_injection(
        func=async_gen,
        container_getter=lambda args, kwargs: kwargs[_CONTAINER_PARAM.name],
        additional_params=[_CONTAINER_PARAM],
        manage_scope=True,
        is_async=False,
    )
    await anext(aiter(wrapped_func(**{_CONTAINER_PARAM.name: container})))

    mock.assert_called_once()


@pytest.mark.asyncio
async def test_async_func_container_getter_with_additional_param_acontainer(
    async_container: AsyncContainer,
    app_provider: AppProvider,
) -> None:
    mock = app_provider.mock

    wrapped_func = wrap_injection(
        func=async_func,
        container_getter=lambda args, kwargs: kwargs[_CONTAINER_PARAM.name],
        additional_params=[_CONTAINER_PARAM],
        manage_scope=True,
        is_async=True,
    )
    await wrapped_func(**{_CONTAINER_PARAM.name: async_container})

    mock.assert_called_once()


@pytest.mark.asyncio
async def test_async_gen_container_getter_with_additional_param_acontainer(
    async_container: AsyncContainer,
    app_provider: AppProvider,
) -> None:
    mock = app_provider.mock

    wrapped_func = wrap_injection(
        func=async_gen,
        container_getter=lambda args, kwargs: kwargs[_CONTAINER_PARAM.name],
        additional_params=[_CONTAINER_PARAM],
        manage_scope=True,
        is_async=True,
    )
    await anext(
        aiter(wrapped_func(**{_CONTAINER_PARAM.name: async_container})),
    )

    mock.assert_called_once()
