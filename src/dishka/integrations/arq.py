__all__ = [
    "inject",
    "setup_dishka",
]

import logging
from typing import Any, Final

from arq import Worker
from arq.typing import StartupShutdown

from dishka.async_container import AsyncContainer
from dishka.integrations.base import wrap_injection

DISHKA_CONTAINER_KEY: Final = "dishka_container"

logger = logging.getLogger(__name__)


def inject(func):
    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda p, _: p[0][DISHKA_CONTAINER_KEY],
        is_async=True,
    )


def job_start(hook_func: StartupShutdown | None):
    async def wrapper(context: dict[Any, Any]) -> None:
        container: AsyncContainer = context["__container__"]
        sub_container = await container().__aenter__()
        context[DISHKA_CONTAINER_KEY] = sub_container

        if hook_func:
            await hook_func(context)

    return wrapper


def job_end(hook_func: StartupShutdown | None):
    async def wrapper(context: dict[Any, Any]) -> None:
        if hook_func:
            await hook_func(context)

        sub_container: AsyncContainer = context[DISHKA_CONTAINER_KEY]
        await sub_container.close()

    return wrapper


def setup_dishka(container: AsyncContainer, worker: Worker) -> None:
    worker.ctx["__container__"] = container
    worker.on_job_start = job_start(worker.on_job_start)
    worker.on_job_end = job_end(worker.on_job_end)
