"""Example typer app greeting a user, taken from
https://typer.tiangolo.com/#example-upgrade with small modifications.
"""

from typing import Annotated, Protocol
import typer
from functools import partial
from dishka import make_container, Provider
from dishka.entities.scope import Scope
from dishka.integrations.typer import FromDishka, inject, setup_dishka


class Greeter(Protocol):
    """Protocol to be extra generic on our greeting infrastructure."""
    def __call__(self, text: str) -> None: ...


provider = Provider(scope=Scope.APP)

# We provide an advanced greeting experience with `typer.secho`
# For a less advanced implementation, we could use `print`
provider.provide(lambda: partial(typer.secho, fg="blue"), provides=Greeter)


app = typer.Typer()


# Setup dishka to inject the dependency container
# Can be done before or after defining the commands when using @inject manually
container = make_container(provider)
setup_dishka(container=container, app=app, auto_inject=False)


@app.command()
@inject
def hello(
    greeter: FromDishka[Greeter],
    name: Annotated[str, typer.Argument(..., help="The name to greet")],
) -> None:
    greeter(f"Hello {name}")


@app.command()
@inject
def goodbye(greeter: FromDishka[Greeter], name: str, formal: bool = False) -> None:
    if formal:
        greeter(f"Goodbye Ms. {name}. Have a good day.")
    else:
        greeter(f"Bye {name}!")


if __name__ == "__main__":
    app()
