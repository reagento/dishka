from faststream import ContextRepo, FastStream, Logger
from faststream.broker.message import StreamMessage
from faststream.nats import NatsBroker

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.faststream import FromDishka, setup_dishka

broker = NatsBroker()
app = FastStream(broker)


class MyProvider(Provider):
    @provide(scope=Scope.APP)
    def get_int(self) -> int:
        return 1


container = make_async_container(MyProvider())
setup_dishka(container, app, auto_inject=True)


@broker.subscriber("test")
async def handler(
    msg,
    logger: Logger,
    m: FromDishka[StreamMessage],
    context: FromDishka[ContextRepo],
):
    logger.info(context)


@app.after_startup
async def t():
    await broker.publish("Hi!", "test")
