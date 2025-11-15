.. _strawberry:

Strawberry
===========================================

Though it is not required, you can use *dishka-strawberry* integration. It features:

* automatic injection of dependencies into GraphQL resolver functions
* integration with FastAPI through ``strawberry.fastapi.GraphQLRouter``


How to use
****************

.. note::
    We suppose that you are using ``AsyncContainer`` with ``Strawberry``.
    Strawberry GraphQL is typically used with FastAPI integration, so you need to setup dishka for FastAPI as well.


1. Import

..  code-block:: python

    from dishka.integrations.strawberry import (
        FromDishka,
        inject,
    )
    from dishka.integrations.fastapi import (
        FastapiProvider,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``FastapiProvider`` as a base class if you need to access ``fastapi.Request`` in your providers

.. code-block:: python

    class AppProvider(FastapiProvider):
        @provide(scope=Scope.REQUEST)
        def create_message(self) -> Message:
             return Message("42")

3. Mark resolver parameters which are to be injected with ``FromDishka[]`` and decorate them using ``@inject``

.. code-block:: python

    @strawberry.type
    class Query:
        @strawberry.field
        @inject
        def answer(self, message: FromDishka[Message]) -> MessageGQL:
            return MessageGQL(message=message)


4. Create Strawberry schema and integrate it with FastAPI using ``GraphQLRouter``

.. code-block:: python

    schema = strawberry.Schema(query=Query)
    graphql_router = GraphQLRouter(schema)

    app = FastAPI()
    app.include_router(graphql_router, prefix="/graphql")


5. Setup ``dishka`` integration for FastAPI (which will handle the container lifecycle for GraphQL requests as well)

.. code-block:: python

    container = make_async_container(AppProvider())
    setup_dishka(container=container, app=app)


Full Example
****************

.. code-block:: python

    from typing import NewType

    import strawberry
    from fastapi import FastAPI
    from strawberry.fastapi import GraphQLRouter

    from dishka import Scope, make_async_container, provide
    from dishka.integrations.fastapi import FastapiProvider, setup_dishka
    from dishka.integrations.strawberry import FromDishka, inject

    Message = NewType("Message", str)

    @strawberry.type(name="Message")
    class MessageGQL:
        message: str


    @strawberry.type
    class Query:
        @strawberry.field
        @inject
        def answer(self, message: FromDishka[Message]) -> MessageGQL:
            return MessageGQL(message=message)


    class AppProvider(FastapiProvider):
        @provide(scope=Scope.REQUEST)
        def get_message(self) -> Message:
            return Message("42")


    def create_app() -> FastAPI:
        schema = strawberry.Schema(query=Query)
        graphql_router = GraphQLRouter(schema)

        app = FastAPI()
        app.include_router(graphql_router, prefix="/graphql")

        container = make_async_container(AppProvider())
        setup_dishka(container, app)

        return app
