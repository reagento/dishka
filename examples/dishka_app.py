from abc import abstractmethod
from typing import Protocol

from dishka import (
    DishkaApp,
    DishkaModule,
    FromDishka,
    Provider,
    Scope,
    make_container,
    provide,
)


# app core
class DbGateway(Protocol):
    @abstractmethod
    def get(self) -> str:
        raise NotImplementedError


class FakeDbGateway(DbGateway):
    def get(self) -> str:
        return "Hello"


class Interactor:
    def __init__(self, db: DbGateway) -> None:
        self.db = db

    def __call__(self) -> str:
        return self.db.get()


# app dependency logic
class AdaptersProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_db(self) -> DbGateway:
        return FakeDbGateway()


class InteractorProvider(Provider):
    interactor = provide(Interactor, scope=Scope.REQUEST)


# presentation layer
handlers = DishkaModule()


@handlers.inject
def index(*, interactor: FromDishka[Interactor]) -> str:
    return interactor()


class Commands:
    @handlers.inject
    def report(self, *, interactor: FromDishka[Interactor]) -> str:
        return interactor()


# application assembly
def main() -> None:
    container = make_container(AdaptersProvider(), InteractorProvider())
    with DishkaApp(container) as app:
        app.include(handlers)
        print(index())
        print(Commands().report())


if __name__ == "__main__":
    main()
