import sqlite3

from typing import Protocol, Iterable
from sqlite3 import Connection

class DAO(Protocol):
    ...

class Service:
    def __init__(self, dao: DAO):
        ...

class DAOImpl(DAO):
    def __init__(self, connection: Connection):
        ...

class SomeClient:
    ...

from dishka import Provider, Scope

service_provider = Provider(scope=Scope.REQUEST)
service_provider.provide(Service)
service_provider.provide(DAOImpl, provides=DAO)
service_provider.provide(SomeClient, scope=Scope.APP)  # override provider scope

from dishka import Provider, provide, Scope

class ConnectionProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def new_connection(self) -> Iterable[Connection]:
        conn = sqlite3.connect(":memory:")
        yield conn
        conn.close()


from dishka import make_container

container = make_container(service_provider, ConnectionProvider())

client = container.get(SomeClient)  # `SomeClient` has Scope.APP, so it is accessible here
client = container.get(SomeClient)  # same instace of `SomeClient`


# subcotaniner to access more short-living objects
with container() as request_container:
    service = request_container.get(Service)
    service = request_container.get(Service)  # same service instance
# at this point connection will be closed as we exited context manager

# new subcontainer to have a new lifespan for request processing
with container() as request_container:
    service = request_container.get(Service)  # new service instance

container.close()
