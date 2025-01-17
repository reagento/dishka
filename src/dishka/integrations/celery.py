__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
    "DishkaTask",
]

from collections.abc import Callable
from typing import Any, Final, ParamSpec, TypeVar

from celery import Celery, Task, current_app
from celery.signals import task_postrun, task_prerun
from celery.utils.functional import head_from_fun

from dishka import Container, FromDishka
from dishka.integrations.base import is_dishka_injected, wrap_injection

CONTAINER_NAME: Final = "dishka_container"
CONTAINER_NAME_REQ: Final = "dishka_container_req"


T = TypeVar("T")
P = ParamSpec("P")


def inject(func: Callable[P, T]) -> Callable[P, T]:
    return wrap_injection(
        func=func,
        is_async=False,
        container_getter=lambda args, kwargs: current_app.conf[
            CONTAINER_NAME_REQ
        ],
    )


def setup_dishka(container: Container, app: Celery):
    app.conf[CONTAINER_NAME] = container


@task_prerun.connect()
def enter_scope(
    task_id,
    task: Task,
    args,
    kwargs: dict[str, Any],
    **other,
) -> None:
    if CONTAINER_NAME in task.app.conf:
        container: Container = task.app.conf[CONTAINER_NAME]
        task.app.conf[CONTAINER_NAME_REQ] = container().__enter__()


@task_postrun.connect()
def exit_scope(
    task_id,
    task,
    args,
    kwargs: dict[str, Any],
    retval,
    **other,
) -> None:
    if CONTAINER_NAME_REQ in task.app.conf:
        container: Container = task.app.conf.pop(CONTAINER_NAME_REQ)
        container.close()


class DishkaTask(Task):
    def __init__(self) -> None:
        super().__init__()

        run = self.run

        if not is_dishka_injected(run):
            injected_func = inject(run)
            self.run = injected_func

            self.__header__ = head_from_fun(injected_func)
