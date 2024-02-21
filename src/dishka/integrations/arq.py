__all__ = [
    "inject",
    "setup_dishka",
]

import logging
from typing import Any, Final

from arq import Worker

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


async def job_start(context: dict[Any, Any]):
    container: AsyncContainer = context["__container__"]
    sub_container = await container().__aenter__()
    context[DISHKA_CONTAINER_KEY] = sub_container


async def job_end(context: dict[Any, Any]) -> None:
    sub_container: AsyncContainer = context[DISHKA_CONTAINER_KEY]
    await sub_container.close()


def setup_dishka(container: AsyncContainer, worker: Worker) -> None:
    if any((worker.on_job_start, worker.on_job_end)):
        logger.warning("Dishka setup will override existing worker hooks")

    worker.ctx["__container__"] = container
    worker.on_job_start = job_start
    worker.on_job_end = job_end
