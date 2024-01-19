import asyncio
from contextlib import asynccontextmanager
from enum import auto

from dishka import provide, Scope, Provider, make_async_container


class MyScope(Scope):
    APP = auto()
    REQUEST = auto()


class MyProvider(Provider):
    def __init__(self, a: int):
        super().__init__()
        self.a = a

    @provide(scope=MyScope.APP)
    @asynccontextmanager
    async def get_int(self) -> int:
        print("solve int")
        yield self.a

    @provide(scope=MyScope.REQUEST)
    @asynccontextmanager
    async def get_str(self, dep: int) -> str:
        print("solve str")
        yield f">{dep}<"


async def main():
    container = make_async_container(
        MyProvider(1), scopes=MyScope, with_lock=True,
    )
    print(await container.get(int))

    async with container() as c_request:
        print(await c_request.get(str))

    async with container() as c_request:
        print(await c_request.get(str))
    await container.close()


if __name__ == '__main__':
    asyncio.run(main())
