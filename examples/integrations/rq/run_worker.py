from redis import Redis

from dishka import Provider, Scope, make_container, provide
from dishka.integrations.rq import DishkaWorker


class StrProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def hello(self) -> str:
        return "Hello"


def setup_worker() -> DishkaWorker:
    provider = StrProvider()
    container = make_container(provider)
    queues = ["default"]
    conn = Redis()
    worker = DishkaWorker(container=container, queues=queues, connection=conn)
    return worker


if __name__ == "__main__":
    worker = setup_worker()
    worker.work(with_scheduler=True)
