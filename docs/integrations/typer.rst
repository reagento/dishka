.. _typer:

Typer
=================================


Though it is not required, you can use dishka-click integration. It features:

* automatic APP and REQUEST scope management
* automatic injection of dependencies into handler function
* passing ``typer.Context`` object as a context data to providers
* you can still request ``typer.Context`` as with usual typer commands


How to use
****************

1. Import

.. code-block:: python

    from dishka.integrations.typer import setup_dishka, inject, TyperProvider


2. Create provider. You can use ``typer.Context`` as a factory parameter to access on REQUEST-scope.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def command_name(self, context: typer.Context) -> str | None:
            return context.command.name


3. *(optional)* Use ``TyperProvider()`` when creating your container if you are using ``typer.Context`` in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), Typerprovider())


4. Mark those of your command handlers parameters which are to be injected with ``FromDishka[]``. You can use ``typer.Context`` in the command as usual.

.. code-block:: python

    app = typer.Typer()

    @app.command(name="greet")
    def greet_user(ctx: typer.Context, greeter: FromDishka[Greeter], user: Annotated[str, typer.Argument()]) -> None:
        ...

4a. *(optional)* decorate commands using ``@inject`` if you want to mark them explicitly

.. code-block:: python

    @app.command(name="greet")
    @inject  # Use this decorator *before* the command decorator
    def greet_user(greeter: FromDishka[Greeter], user: Annotated[str, typer.Argument()]) -> None:
        ...


5. *(optional)* Use ``auto_inject=True`` when setting up dishka to automatically inject dependencies into your command handlers. When doing this, ensure all commands have already been created when you call setup. This limitation is not required when using ``@inject`` manually.

.. code-block:: python

    setup_dishka(container=container, app=app, auto_inject=True)
