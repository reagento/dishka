"""Example typer app greeting a user, taken from
https://typer.tiangolo.com/#example-upgrade with small modifications.
"""

from typing import Annotated, Protocol
import typer
from functools import partial
from dishka import make_container, Provider, provide
from dishka.entities.scope import Scope
from dishka.integrations.typer import FromDishka, TyperProvider, inject, setup_dishka


class Greeter(Protocol):
    """Protocol to be extra generic on our greeting infrastructure."""
    def __call__(self, text: str) -> None: ...


class ColorfulProvider(Provider):

    @provide(scope=Scope.REQUEST)  # We need Scope.REQUEST for the context
    def greeter(self, context: typer.Context) -> Greeter:
        if context.command.name == "hello":
            # Hello should most certainly be blue
            return partial(typer.secho, fg="blue")
        if context.command.name == "goodbye":
            # Goodbye should be red
            return partial(typer.secho, fg="red")
        # Unexpected commands can be yellow
        return partial(typer.secho, fg="yellow")


app = typer.Typer()


@app.command()
def hello(
    greeter: FromDishka[Greeter],
    name: Annotated[str, typer.Argument(..., help="The name to greet")],
) -> None:
    greeter(f"Hello {name}")


@app.command()
def goodbye(greeter: FromDishka[Greeter], name: str, formal: bool = False) -> None:
    if formal:
        greeter(f"Goodbye Ms. {name}. Have a good day.")
    else:
        greeter(f"Bye {name}!")


@app.command()
def hi(
    greeter: FromDishka[Greeter],
    name: Annotated[str, typer.Argument(..., help="The name to greet")],
) -> None:
    greeter(f"Hi {name}")


# Build the container with the `TyperProvider` to get the `typer.Context`
# parameter in REQUEST providers
container = make_container(ColorfulProvider(scope=Scope.REQUEST), TyperProvider())

# Setup dishka to inject the dependency container
# *Must* be after defining the commands when using auto_inject
setup_dishka(container=container, app=app, auto_inject=True)


if __name__ == "__main__":
    app()

