__all__ = [
    "inject",
    "setup_dishka",
]

import logging
from typing import Any, Final

from arq import Worker
from dishka import Provider, make_async_container
from dishka.async_container import AsyncContextWrapper
from dishka.integrations.base import wrap_injection


CONTAINER_KEY: Final = "dishka_container"

logger = logging.getLogger(__name__)


def inject(func):
    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda p, _: p[0][CONTAINER_KEY],
        is_async=True,
    )


def startup(wrapper_container: AsyncContextWrapper):
    async def wrapper(context: dict[Any, Any]) -> None:
        context["__container__"] = await wrapper_container.__aenter__()

    return wrapper


def shutdown(wrapper_container: AsyncContextWrapper):
    async def wrapper(context: dict[Any, Any]) -> None:
        await wrapper_container.__aexit__(None, None, None)

    return wrapper


async def job_start(context: dict[Any, Any]) -> None:
    sub_container = await context["__container__"]().__aenter__()
    context[CONTAINER_KEY] = sub_container


async def job_end(context: dict[Any, Any]) -> None:
    await context["__container__"]().__aexit__(None, None, None)


def setup_dishka(*providers: Provider, worker: Worker) -> None:
    if any(
        (worker.on_startup, worker.on_shutdown, worker.on_job_start, worker.on_job_end)
    ):
        logger.warning("Dishka setup will override existing worker hooks")

    wrapper_container = make_async_container(*providers)
    worker.on_startup = startup(wrapper_container)
    worker.on_shutdown = shutdown(wrapper_container)
    worker.on_job_start = job_start
    worker.on_job_end = job_end
