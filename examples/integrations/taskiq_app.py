import asyncio
import random

from taskiq import AsyncTaskiqTask, InMemoryBroker

from dishka import FromDishka, Provider, Scope, make_async_container
from dishka.integrations.taskiq import inject, setup_dishka, TaskiqProvider

provider = Provider(scope=Scope.REQUEST)
provider.provide(lambda: random.random(), provides=float)  # noqa: S311

broker = InMemoryBroker()


@broker.task
@inject
async def random_task(num: FromDishka[float]) -> float:
    raise ValueError


async def main() -> None:
    container = make_async_container(provider, TaskiqProvider())
    setup_dishka(container, broker)
    await broker.startup()

    task: AsyncTaskiqTask[float] = await random_task.kiq()
    result = await task.wait_result()
    print(result.return_value)  # noqa: T201

    await broker.shutdown()
    await container.close()


if __name__ == "__main__":
    asyncio.run(main())
