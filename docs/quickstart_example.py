import sqlite3
from collections.abc import Iterable
from sqlite3 import Connection
from typing import Protocol

from dishka import Provider, Scope, make_container, provide


class APIClient:
    ...


class UserDAO(Protocol):
    ...


class SQLiteUserDAO(UserDAO):
    def __init__(self, connection: Connection):
        ...


class Service:
    def __init__(self, client: APIClient, user_dao: UserDAO):
        ...


service_provider = Provider(scope=Scope.REQUEST)
service_provider.provide(Service)
service_provider.provide(SQLiteUserDAO, provides=UserDAO)
service_provider.provide(APIClient, scope=Scope.APP)  # override provider's scope


class ConnectionProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def new_connection(self) -> Iterable[Connection]:
        connection = sqlite3.connect(":memory:")
        yield connection
        connection.close()


container = make_container(service_provider, ConnectionProvider())

# APIClient is bound to Scope.APP, so it can be accessed here
# or from any scope inside including Scope.REQUEST
client = container.get(APIClient)
client = container.get(APIClient)  # the same APIClient instance as above

# A sub-container to access shorter-living objects
with container() as request_container:
    # Service, UserDAO implementation, and Connection are bound to Scope.REQUEST,
    # so they are accessible here. APIClient can also be accessed here
    service = request_container.get(Service)
    service = request_container.get(Service)  # the same Service instance as above

# Since we exited the context manager, the sqlite3 connection is now closed

# A new sub-container has a new lifespan for request processing
with container() as request_container:
    service = request_container.get(Service)  # a new Service instance

container.close()
