from typing import Annotated

from faststream import FastStream
from faststream.nats import NatsBroker

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.faststream import Depends, inject, setup_dishka


class A:
    def __init__(self) -> None:
        pass


class B:
    def __init__(self, a: A) -> None:
        self.a = a


class MyProvider(Provider):
    @provide(scope=Scope.APP)
    def get_a(self) -> A:
        return A()

    @provide(scope=Scope.REQUEST)
    def get_b(self, a: A) -> B:
        return B(a)


provider = MyProvider()
container = make_async_container(provider)

broker = NatsBroker()
app = FastStream(broker)
setup_dishka(container, app)


@broker.subscriber("test")
@inject
async def handler(
    msg: str,
    a: Annotated[A, Depends()],
    b: Annotated[B, Depends()],
):
    print(msg, a, b)


@app.after_startup
async def t():
    await broker.publish("test", "test")
