__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
    "DishkaTask",
]

from collections.abc import Callable
from inspect import Parameter
from typing import Any, Final, ParamSpec, TypeVar

from celery import Celery, Task
from celery.signals import task_postrun, task_prerun

from dishka import Container, FromDishka
from dishka.integrations.base import is_dishka_injected, wrap_injection

CONTAINER_NAME: Final = "dishka_container"


T = TypeVar("T")
P = ParamSpec("P")


def inject(func: Callable[P, T]) -> Callable[P, T]:
    additional_params = [
        Parameter(
            name=CONTAINER_NAME,
            annotation=Container,
            kind=Parameter.KEYWORD_ONLY,
        ),
    ]
    return wrap_injection(
        func=func,
        is_async=False,
        remove_depends=True,
        additional_params=additional_params,
        container_getter=lambda args, kwargs: kwargs[CONTAINER_NAME],
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
        kwargs[CONTAINER_NAME] = container().__enter__()


@task_postrun.connect()
def exit_scope(
    task_id,
    task,
    args,
    kwargs: dict[str, Any],
    retval,
    **other,
) -> None:
    if CONTAINER_NAME in kwargs:
        container: Container = kwargs[CONTAINER_NAME]
        container.close()


class DishkaTask(Task):
    def __init__(self) -> None:
        super().__init__()

        run = self.run

        if not is_dishka_injected(run):
            self.run = inject(run)
