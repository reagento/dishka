from collections.abc import Iterable
from sqlite3 import connect, Connection

from dishka import Provider, Scope, provide, make_async_container
from dishka.integrations.fastapi import setup_dishka


class ConnectionProvider(Provider):
    def __init__(self, uri):
        super().__init__()
        self.uri = uri

    @provide(scope=Scope.REQUEST)
    def get_connection(self) -> Iterable[Connection]:
        conn = connect(self.uri)
        yield conn
        conn.close()


container = make_async_container(ConnectionProvider("sqlite:///"))
setup_dishka(container, app)
