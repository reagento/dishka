from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from dishka import Provider, Scope, alias, make_container, provide


@dataclass
class Config:
    value: int


class Gateway(Protocol):
    pass


class Connection:
    def close(self):
        print("Connection closed")


class GatewayImplementation(Gateway):
    def __init__(self, config: Config, connection: Connection):
        self.value = config.value
        self.connection = connection

    def __repr__(self):
        return f"A(value={self.value}, connection={self.connection})"


class MyProvider(Provider):
    scope = Scope.REQUEST

    def __init__(self, config: Config):
        super().__init__()
        self.config = config

    # simple factory with explicit scope
    @provide(scope=Scope.APP)
    def get_config(self) -> Config:
        return self.config

    # object with finalization and provider-defined scope
    @provide
    def get_conn(self) -> Iterable[Connection]:
        connection = Connection()
        yield connection
        connection.close()

    # object by `__init__`
    gw = provide(GatewayImplementation)
    # another type for same object
    base_gw = alias(source=GatewayImplementation, provides=Gateway)


def main():
    config = Config(1)
    provider = MyProvider(config)
    container = make_container(provider)

    print(container.get(Config))
    with container() as c_request:
        print(c_request.get(GatewayImplementation))
        print(c_request.get(Gateway))
    with container() as c_request:
        print(c_request.get(Gateway))

    container.close()


if __name__ == '__main__':
    main()
