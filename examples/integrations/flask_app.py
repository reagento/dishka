from abc import abstractmethod
from typing import Annotated, Protocol

from flask import Flask

from dishka import (
    Provider,
    Scope,
    make_container,
    provide,
)
from dishka.integrations.flask import (
    FlaskProvider,
    FromDishka,
    inject,
    setup_dishka,
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
    def __init__(self, db: DbGateway):
        self.db = db

    def __call__(self) -> str:
        return self.db.get()


# app dependency logic
class AdaptersProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_db(self) -> DbGateway:
        return FakeDbGateway()


class InteractorProvider(Provider):
    i1 = provide(Interactor, scope=Scope.REQUEST)


# presentation layer
app = Flask(__name__)


@app.get("/")
@inject
def index(
        *,
        interactor: FromDishka[Interactor],
) -> str:
    result = interactor()
    return result


@app.get("/auto")
def auto(
        *,
        interactor: FromDishka[Interactor],
) -> str:
    result = interactor()
    return result


container = make_container(AdaptersProvider(), InteractorProvider(), FlaskProvider())
setup_dishka(container=container, app=app, auto_inject=True)
try:
    app.run()
finally:
    container.close()
