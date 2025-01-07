.. _typer:

Typer
=================================


Though it is not required, you can use dishka-click integration. It features automatic injection to command handlers
In contrast with other integrations there is no scope management.



How to use
****************

1. Import

.. code-block:: python

    from dishka.integrations.typer import setup_dishka, inject


2. Create a container and set it up with the typer app. Pass ``auto_inject=True`` if you do not want to use the ``@inject`` decorator explicitly.

.. code-block:: python

    app = typer.Typer()

    container = make_container(MyProvider())
    setup_dishka(container=container, app=app, auto_inject=True)


3. Mark those of your command handlers parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

    app = typer.Typer()

    @app.command(name="greet")
    def greet_user(greeter: FromDishka[Greeter], user: Annotated[str, typer.Argument()]) -> None:
        ...

3a. *(optional)* decorate them using ``@inject`` if you want to mark commands explicitly

.. code-block:: python

    @app.command(name="greet")
    @inject  # Use this decorator *before* the command decorator
    def greet_user(greeter: FromDishka[Greeter], user: Annotated[str, typer.Argument()]) -> None:
        ...
