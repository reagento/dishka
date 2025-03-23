import random

from celery import Celery

from dishka import Provider, Scope, make_container
from dishka.integrations.celery import FromDishka, inject, setup_dishka

provider = Provider(scope=Scope.REQUEST)
provider.provide(lambda: random.random(), provides=float)  # noqa: S311


app = Celery()


@app.task
@inject
def random_task(num: FromDishka[float]) -> float:
    return num


def main() -> None:
    container = make_container(provider)
    setup_dishka(container, app)

    result = random_task.apply()

    print(result.get())  # noqa: T201

    container.close()


if __name__ == "__main__":
    main()
