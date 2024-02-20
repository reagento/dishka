import logging
from typing import Protocol, Annotated, Any

from arq import Worker
from arq.connections import RedisSettings
from dishka import Provider, Scope, provide
from dishka.integrations.base import Depends
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
    gateway: Annotated[Gateway, Depends()],
):
    result = await gateway.get()
    logger.info(result)


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s  %(process)-7s %(module)-20s %(message)s",
    )

    worker = Worker(functions=[get_content], redis_settings=RedisSettings())  # type: ignore
    setup_dishka(GatewayProvider(), worker=worker)
    worker.run()


if __name__ == "__main__":
    main()
