import asyncio
from abc import abstractmethod
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar

import click
from dishka import (
    FromDishka,
    Provider,
    Scope,
    make_container,
    provide,
)
from dishka.integrations.click import setup_dishka


class DbGateway(Protocol):
    @abstractmethod
    async def get(self) -> str:
        raise NotImplementedError


class FakeDbGateway(DbGateway):
    async def get(self) -> str:
        await asyncio.sleep(0.1)
        return "Hello123"


class Interactor:
    def __init__(self, db: DbGateway) -> None:
        self.db = db

    async def __call__(self) -> str:
        return await self.db.get()


class AdaptersProvider(Provider):
    @provide(scope=Scope.APP)
    def get_db(self) -> DbGateway:
        return FakeDbGateway()


class InteractorProvider(Provider):
    i1 = provide(Interactor, scope=Scope.APP)


P = ParamSpec("P")
T = TypeVar("T")


def async_command(f: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, T]:
    @wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group()
@click.pass_context
def main(context: click.Context) -> None:
    container = make_container(AdaptersProvider(), InteractorProvider())
    setup_dishka(container=container, context=context, auto_inject=True)


@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
@async_command
async def hello(
        count: int,
        name: str,
        interactor: FromDishka[Interactor],
) -> None:
    """Simple program that greets NAME for a total of COUNT times."""
    for _ in range(count):
        click.echo(f"Hello {name}!")
        click.echo(await interactor())


main.add_command(hello, name="hello")

if __name__ == "__main__":
    main()
