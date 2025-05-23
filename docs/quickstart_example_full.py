import sqlite3
from collections.abc import Iterable
from sqlite3 import Connection
from typing import Protocol

from dishka import Provider, Scope, make_container, provide


class DAO(Protocol): ...


class Service:
    def __init__(self, dao: DAO): ...


class DAOImpl(DAO):
    def __init__(self, connection: Connection): ...


class SomeClient: ...


service_provider = Provider(scope=Scope.REQUEST)
service_provider.provide(Service)
service_provider.provide(DAOImpl, provides=DAO)
service_provider.provide(
    SomeClient,
    scope=Scope.APP,
)  # override provider scope


class ConnectionProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def new_connection(self) -> Iterable[Connection]:
        conn = sqlite3.connect(":memory:")
        yield conn
        conn.close()


container = make_container(service_provider, ConnectionProvider())

client = container.get(
    SomeClient,
)  # `SomeClient` has Scope.APP, so it is accessible here
client = container.get(SomeClient)  # same instance of `SomeClient`

# subcontainer to access shorter-living objects
with container() as request_container:
    service = request_container.get(Service)
    service = request_container.get(Service)  # same service instance
# since we exited the context manager, the connection is now closed

# new subcontainer to have a new lifespan for request processing
with container() as request_container:
    service = request_container.get(Service)  # new service instance

container.close()
