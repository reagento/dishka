import asyncio
import logging
from typing import Protocol, Annotated, Any

from arq.worker import create_worker
from dishka import Provider, Scope, provide, make_async_container, FromDishka
from dishka.integrations.arq import inject, setup_dishka

logger = logging.getLogger(__name__)


class Gateway(Protocol):
    async def get(self) -> int: ...


class MockGateway(Gateway):
    async def get(self) -> int:
        return hash(self)


class GatewayProvider(Provider):
    get_gateway = provide(MockGateway, scope=Scope.REQUEST, provides=Gateway)


@inject
async def get_content(
    context: dict[Any, Any],
    gateway: FromDishka[Gateway],
):
    result = await gateway.get()
    logger.info(result)


class WorkerSettings:
    functions = [get_content]


async def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s  %(process)-7s %(module)-20s %(message)s",
    )

    worker = create_worker(WorkerSettings)

    container = make_async_container(GatewayProvider())
    setup_dishka(container=container, worker_settings=worker)

    try:
        await worker.async_run()
    finally:
        await container.close()
        await worker.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError:  # happens on shutdown, fine
        pass
