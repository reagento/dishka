import sqlite3
from collections.abc import Iterable
from sqlite3 import Connection

from dishka import Provider, Scope, provide


class ConnectionProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def new_connection(self) -> Iterable[Connection]:
        connection = sqlite3.connect(":memory:")
        yield connection
        connection.close()
