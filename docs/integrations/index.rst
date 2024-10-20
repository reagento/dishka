.. include:: <isonum.txt>

Using with frameworks
*******************************

There are some integrations in library, however you are not limited to them only.
You can create custom integrations for your framework of choice.

Built-in frameworks integrations includes:

.. toctree::
   :hidden:

   aiogram
   aiogram_dialog
   aiohttp
   click
   fastapi
   faststream
   flask
   litestar
   sanic
   starlette
   taskiq
   telebot
   adding_new

Web frameworks
    * :ref:`aiohttp`
    * grpcio
    * :ref:`Fastapi`
    * :ref:`Flask`
    * :ref:`Litestar`
    * :ref:`Sanic`
    * :ref:`Starlette`

Telegram bots
    * :ref:`aiogram`
    * :ref:`Aiogram_dialog`
    * :ref:`pyTelegramBotAPI<telebot>`

Tasks and events
    * Arq
    * :ref:`FastStream`
    * :ref:`TaskIq`

Other
    * :ref:`Click`

See real `integation examples <https://github.com/reagento/dishka/tree/develop/examples/integrations>`_ here.

:ref:`adding_new`

Common approach
=====================

For several frameworks library contains helper functions so you don't need to control scopes yourself, but just annotate handler/view functions and change application startup code

To use framework integration you mainly need to do 3 things:

* call ``setup_dishka`` on your container and framework entity
* add ``FromDishka[YourClass]`` on you framework handlers (or view-functions)
* decorate your handlers with ``@inject`` before registering them in framework. Some integrations do not required it, see their details

.. note::
   ``FromDishka[T]`` is basically a synonym for ``Annotated[T, FromComponent()]`` and is used to get an object from default component. To use other component you can use the same syntax with annotated ``Annotated[T, FromComponent("X")]``.

   For more details on components see :ref:`components`

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

For some frameworks like ``grpcio`` common approach is not suitable. You need to create ``DishkaInterceptor`` or ``DishkaAioInterceptor`` and pass in to your server.
But you still use ``@inject`` on your servicer methods. E.g.:

.. code-block:: python

    from dishka.integrations.grpcio import (
        DishkaInterceptor,
        FromDishka,
        inject,
    )
    server = grpc.server(
        ThreadPoolExecutor(max_workers=10),
        interceptors=[
            DishkaInterceptor(container),
        ],
    )

    class MyServiceImpl(MyServicer):
        @inject
        def MyMethod(
                self,
                request: MyRequest,
                context: grpc.ServicerContext,
                a: FromDishka[RequestDep],
        ) -> MyResponse:
            ...


.. _autoinject:

Context data
====================

As ``REQUEST`` scope is entered automatically you cannot pass context data directly, but integrations do it for you:

These objects are passed to context:

* aiohttp - ``aiohttp.web_request.Request``. Provider ``AiohttpProvider``.
* Flask - ``flask.Request``. Provider ``FlaskProvider``.
* Fastapi - ``fastapi.Request`` or ``fastapi.WebSocket`` if you are using web sockets. Provider ``StarletteProvider``.
* Litestar - ``litestar.Request``. Provider ``LitestarProvider``.
* Starlette - ``starlette.requests.Request`` or ``starlette.websockets.WebSocket`` if you are using web sockets. Provider ``StarletteProvider``.
* Aiogram - ``aiogram.types.TelegramObject``. Provider ``AiogramProvider``
* pyTelegramBotAPI - ``dishka.integrations.telebot.TelebotMessage`` Provider ``TelebotProvider``.
* Arq - no objects and provider.
* FastStream - ``faststream.broker.message.StreamMessage`` or ``dishka.integration.faststream.FastStreamMessage``, ``faststream.utils.ContextRepo``. Provider ``FastStreamProvider``.
* TaskIq - no objects and provider.
* Sanic - ``sanic.request.Request``. Provider ``SanicProvider``
* grpcio - ``grpcio.ServicerContext`` to get the current context and ``google.protobuf.message.Message`` to get the current request. Message is available only for ``unary_unary`` and ``unary_stream`` rpc method. Provider ``GrpcioProvider``.
* Click - no objects and provider.


To access such objects, just specify them as your factory parameter and add corresponding integrations provider when creating a container.


Websocket support
=============================

Injection is working with webosckets in these frameworks:

* FastAPI
* Starlette
* aiohttp

Also it works for grpcio ``stream_*`` rpc methods.

For most cases we operate single events like HTTP-requests. In this case we operate only 2 scopes: ``APP`` and ``REQUEST``. Websockets are different: for one application you have multiple connections (one per client) and each connection delivers multiple messages. To support this we use additional scope: ``SESSION``:

    ``APP`` |rarr| ``SESSION`` |rarr| ``REQUEST``

In frameworks like FastAPI and Starlette your view function is called once per connection and then you retrieve messages in loop. So, ``inject`` decorator can be only used to retrieve SESSION-scoped objects. To achieve REQUEST-scope you can enter in manually:

.. code-block:: python



