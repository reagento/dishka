import asyncio
from contextlib import asynccontextmanager
from enum import auto

from dishka import provide, Scope, Provider, AsyncContainer


class MyScope(Scope):
    APP = auto()
    REQUEST = auto()


class MyProvider(Provider):
    def __init__(self, a: int):
        self.a = a

    @provide(MyScope.APP)
    @asynccontextmanager
    async def get_int(self) -> int:
        print("solve int")
        yield self.a

    @provide(MyScope.REQUEST)
    @asynccontextmanager
    async def get_str(self, dep: int) -> str:
        print("solve str")
        yield f">{dep}<"


async def main():
    container = AsyncContainer(
        MyProvider(1), scope=MyScope.APP, with_lock=True,
    )
    print(await container.get(int))

    async with container() as c_request:
        print(await c_request.get(str))

    async with container() as c_request:
        print(await c_request.get(str))
    await container.close()


if __name__ == '__main__':
    asyncio.run(main())
