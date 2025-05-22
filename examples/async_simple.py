import asyncio
from collections.abc import AsyncIterable
from dataclasses import dataclass
from typing import Protocol

from dishka import Provider, Scope, alias, make_async_container, provide


@dataclass
class Config:
    value: int


class Gateway(Protocol):
    pass


class Connection:
    async def close(self):
        print("Connection closed")


class GatewayImplementation(Gateway):
    def __init__(self, config: Config, connection: Connection):
        self.value = config.value
        self.connection = connection

    def __repr__(self):
        return f"A(value={self.value}, connection={self.connection})"


class MyProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    # simple factory with explicit scope
    @provide(scope=Scope.APP)
    def get_config(self) -> Config:
        return self.config

    # async factory with object finalization and provider-defined scope
    @provide
    async def get_conn(self) -> AsyncIterable[Connection]:
        connection = Connection()
        yield connection
        await connection.close()

    # object by `__init__`
    gw = provide(GatewayImplementation)
    # another type for same object
    base_gw = alias(source=GatewayImplementation, provides=Gateway)


async def main():
    config = Config(1)
    provider = MyProvider(config)
    container = make_async_container(provider)

    print(await container.get(Config))
    async with container() as c_request:
        print(await c_request.get(GatewayImplementation))
        print(await c_request.get(Gateway))
    async with container() as c_request:
        print(await c_request.get(Gateway))

    await container.close()


if __name__ == "__main__":
    asyncio.run(main())
