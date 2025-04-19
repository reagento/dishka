.. _click:

Click
=================================


Though it is not required, you can use ``dishka-click`` integration. It features automatic injection to command handlers
In contrast with other integrations there is no scope management.



How to use
****************

1. Import

.. code-block:: python

    from dishka.integrations.click import setup_dishka, inject

2. Create container in group handler and setup it to click context. Pass ``auto_inject=True`` unless you want to use ``@inject`` decorator explicitly.

.. code-block:: python

    @click.group()
    @click.pass_context
    def main(context: click.Context):
        container = make_container(MyProvider())
        setup_dishka(container=container, context=context, auto_inject=True)


3. Mark those of your command handlers parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

    @main.command(name="hello")
    def hello(interactor: FromDishka[Interactor]):
        ...

3a. *(optional)* decorate them using ``@inject``

.. code-block:: python

    @main.command(name="hello")
    @inject
    def hello(interactor: FromDishka[Interactor]):
        ...