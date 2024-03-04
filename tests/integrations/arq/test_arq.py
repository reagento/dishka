from contextlib import asynccontextmanager
from typing import Annotated, Any
from unittest.mock import Mock

import pytest

from dishka import FromDishka, make_async_container
from dishka.integrations.arq import inject, setup_dishka
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)


class WorkerSettings:
    pass


@asynccontextmanager
async def dishka_app(provider):
    container = make_async_container(provider)
    setup_dishka(container, worker_settings=WorkerSettings)
    yield WorkerSettings
    await container.close()


@inject
async def get_with_app(
    _: dict[str, Any],
    a: Annotated[AppDep, FromDishka()],
    mock: Annotated[Mock, FromDishka()],
) -> None:
    mock(a)


@inject
async def get_with_request(
    _: dict[str, Any],
    a: Annotated[RequestDep, FromDishka()],
    mock: Annotated[Mock, FromDishka()],
) -> None:
    mock(a)


@pytest.mark.asyncio
async def test_app_dependency(app_provider: AppProvider):
    async with dishka_app(app_provider) as settings:
        await settings.on_job_start(settings.ctx)
        await get_with_app(settings.ctx)
        await settings.on_job_end(settings.ctx)
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()

    app_provider.app_released.assert_called()


@pytest.mark.asyncio
async def test_request_dependency(app_provider: AppProvider):
    async with dishka_app(app_provider) as settings:
        await settings.on_job_start(settings.ctx)
        await get_with_request(settings.ctx)
        await settings.on_job_end(settings.ctx)
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.app_released.assert_not_called()
