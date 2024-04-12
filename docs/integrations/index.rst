Using with frameworks
*******************************

There are some integrations in library you are not limited to use them.

Built-in frameworks integrations:

* aiohttp
* Flask
* Fastapi
* Litestar
* Starlette
* Aiogram
* pyTelegramBotAPI
* Arq
* FastStream
* TaskIq

Common approach
=====================

For several frameworks library contains helper functions so you don't need to control scopes yourself, but just annotate handler/view functions and change application startup code

To use framework integration you mainly need to do 3 things:

* call ``setup_dishka`` on your container and framework entity
* add ``FromDishka[YourClass]`` on you framework handlers (or view-functions)
* decorate your handlers with ``@inject`` before registering them in framework. Some integrations do not required it, see :ref:`autoinject`

For FastAPI it will look like:

.. code-block:: python

   from dishka.integrations.fastapi import FromDishka, inject, setup_dishka

   @router.get("/")
   @inject
   async def index(interactor: FromDishka[Interactor]) -> str:
       result = interactor()
       return result

   app = FastAPI()
   container = make_async_container(provider)
   setup_dishka(container, app)


For such integrations library enters scope for each generated event. So if you have standard scope, than handler dependencies will be retrieved as for ``Scope.REQUEST``.

Additionally, you may need to call ``container.close()`` in the end of your application lifecycle if you want to finalize APP-scoped dependencies

.. _autoinject:

Auto injection
=========================

With some frameworks we provide an option to inject dependencies in handlers without decorating them with ``@inject``.

* For **aiogram** you need to provide ``auto_inject=True`` when calling ``setup_dishka``. E.g:

.. code-block:: python

    from dishka.integrations.aiogram import FromDishka, setup_dishka

    @router.message()
    async def start(
        message: Message,
        user: FromDishka[User],
    ):
        await message.answer(f"Hello, {1}, {user.full_name}!")


    setup_dishka(container=container, router=dp, auto_inject=True)

* For **Flask** you need to provide ``auto_inject=True`` when calling ``setup_dishka``. It is important here to call it after registering all views and blueprints. E.g:

.. code-block:: python

    from dishka.integrations.flask import FromDishka, setup_dishka

    @app.get("/")
    def index(
            *,
            interactor: FromDishka[Interactor],
    ) -> str:
        result = interactor()
        return result

    setup_dishka(container=container, app=app, auto_inject=True)

* For **FastAPI** you need to provide ``route_class=DishkaRoute`` when creating ``APIRouter``. E.g.:

.. code-block:: python

    from dishka.integrations.fastapi import FromDishka, DishkaRoute, setup_dishka

    router = APIRouter(route_class=DishkaRoute)

    @router.get("/")
    async def index(
            *,
            interactor: FromDishka[Interactor],
    ) -> str:
        result = interactor()
        return result

    setup_dishka(container, app)

* For **FasStream** (**0.5.0** version and higher) you need to provide ``auto_inject=True`` when calling ``setup_dishka``. It is important here to call it before registering any subscribers or router include:

.. code-block:: python

    from faststream import FastStream
    from faststream.nats import NatsBroker, NatsMessage
    from dishka import make_async_container
    from dishka.integrations.faststream import FastStreamProvider, FromDishka, setup_dishka

    broker = NatsBroker()
    app = FastStream(broker)
    setup_dishka(make_async_container(..., FastStreamProvider), app, auto_inject=True)

    @broker.subscriber("/")
    def index(
            *,
            message: FromDishka[NatsMessage],
    ) -> str:
        await message.ack()
        return message.body


Context data
====================

As ``REQUEST`` scope is entered automatically you cannot pass context data directly, but integrations do it for you:

This objects are passed to context:

* aiohttp - ``aiohttp.web_request.Request``
* Flask - ``flask.Request``
* Fastapi - ``fastapi.Request``
* Litestar - ``litestar.Request``
* Starlette - ``starlette.requests.Request``
* Aiogram - ``aiogram.types.TelegramObject``
* pyTelegramBotAPI - actual type of event (like ``Message``) is used.
* Arq - no objects
* FastStream - ``faststream.broker.message.StreamMessage`` or ``faststream.[broker].[Broker]Message``, ``faststream.utils.ContextRepo`` 
* TaskIq - no objects

To use such objects you need to declare them in your provider using :ref:`from-context` and then they will be available as factories params.


Adding integrations
===========================

Though there are some integrations in library you are not limited to use them.

The main points are:

1. Find a way to pass a global container instance. Often it is attached to application instance or passed by a middleware.
2. Find a place to enter request scope and how to pass it to a handler. Usually, it is entered in a middleware and container is stored in some kind of request context.
3. Configure a decorator. The main option here is to provide a way for retrieving container. Often, need to modify handler signature adding additional parameters. It is also available.
4. Check if you can apply decorator automatically.

While writing middlewares and working with scopes is done by your custom code, we have a helper for creating ``@inject`` decorators - a ``wrap_injection`` function.

* ``container_getter`` is a function with two params ``(args, kwargs)`` which is called to get a container used to retrieve dependencies within scope.
* ``additional_params`` is a list of ``inspect.Parameter`` which should be added to handler signature.

For more details, check existing integrations.
