__all__ = [
    "inject",
    "setup_dishka",
]

import logging
from typing import Any, Final

from arq import Worker
from arq.typing import StartupShutdown, WorkerSettingsType

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


def setup_dishka(
    container: AsyncContainer, worker_settings: WorkerSettingsType | Worker
) -> None:
    if isinstance(worker_settings, dict):
        if worker_settings.get("ctx"):
            worker_settings["ctx"]["__container__"] = container
        else:
            worker_settings["ctx"] = {"__container__": container}

        worker_settings["ctx"] = worker_settings.get("ctx", {}).setdefault(
            "__container__", container
        )
        worker_settings["on_job_start"] = job_start(worker_settings.get("on_job_start"))
        worker_settings["on_job_end"] = job_end(worker_settings.get("on_job_end"))
    else:
        if hasattr(worker_settings, "ctx"):
            worker_settings.ctx["__container__"] = container
        else:
            worker_settings.ctx = {"__container__": container}

        worker_settings.on_job_start = (
            job_start(worker_settings.on_job_start)
            if hasattr(worker_settings, "on_job_start")
            else job_start(None)
        )
        worker_settings.on_job_end = (
            job_end(worker_settings.on_job_end)
            if hasattr(worker_settings, "on_job_end")
            else job_end(None)
        )
