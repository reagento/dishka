import asyncio
from typing import AsyncGenerator, AsyncIterable

from dishka import Provider, Scope, make_async_container, provide


class MyProvider(Provider):
    def __init__(self, a: int):
        super().__init__()
        self.a = a

    @provide(scope=Scope.APP)
    async def get_int(self) -> AsyncIterable[int]:
        print("solve int")
        yield self.a

    @provide(scope=Scope.REQUEST)
    async def get_str(self, dep: int) -> AsyncGenerator[str, None]:
        print("solve str")
        yield f">{dep}<"


async def main():
    async with make_async_container(MyProvider(1)) as container:
        print(await container.get(int))

        async with container() as c_request:
            print(await c_request.get(str))

        async with container() as c_request:
            print(await c_request.get(str))


if __name__ == '__main__':
    asyncio.run(main())
