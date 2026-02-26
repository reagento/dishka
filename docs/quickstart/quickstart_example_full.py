import sqlite3
from collections.abc import Iterable
from sqlite3 import Connection

from dishka import Provider, Scope, make_container, provide


class APIClient:
    ...


class DBGateway:
    def __init__(self, connection: Connection):
        ...


class Service:
    def __init__(self, client: APIClient, db: DBGateway):
        ...


service_provider = Provider(scope=Scope.REQUEST)
service_provider.provide(Service)
service_provider.provide(DBGateway)
service_provider.provide(APIClient, scope=Scope.APP)  # override provider's scope


class ConnectionProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def new_connection(self) -> Iterable[Connection]:
        connection = sqlite3.connect(":memory:")
        yield connection
        connection.close()


container = make_container(service_provider, ConnectionProvider())

# APIClient is bound to Scope.APP, so it is accessible here
client_1 = container.get(APIClient)
client_2 = container.get(APIClient)  # the same APIClient instance
assert client_1 is client_2

# The sub-container to access shorter-living objects
with container() as request_container:
    # Service, DBGateway, and Connection are bound to Scope.REQUEST,
    # so they are accessible here
    service_1 = request_container.get(Service)
    service_2 = request_container.get(Service)  # the same service instance
    assert service_1 is service_2

# Since we exited the context manager, the sqlite3 connection is now closed

# The new subcontainer has a new lifespan for event processing
with container() as request_container:
    service = request_container.get(Service)  # the new service instance
