from faststream import ContextRepo, FastStream
from faststream.nats import NatsBroker, NatsMessage

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.faststream import FromDishka, setup_dishka


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
setup_dishka(container, app, auto_inject=True)


@broker.subscriber("test")
async def handler(
    msg: str,
    a: FromDishka[A],
    b: FromDishka[B],
    raw_message: FromDishka[NatsMessage],
    faststream_context: FromDishka[ContextRepo],
):
    print(msg, a, b)


@app.after_startup
async def t():
    await broker.publish("test", "test")
