.. include:: <isonum.txt>

.. _grpcio:

gRPC
============================

Though it is not required, you can use dishka-grpcio integration. It features:

* automatic REQUEST and SESSION scope management using interceptors
* passing ``Message`` and ``ServicerContext`` objects as a context data to providers for both **unary** and **stream** requests
* injection of dependencies into handler functions using decorators

Both grpc and grpc.aio services are supported.

How to use
****************

1. Import

.. code-block:: python

    from dishka.integrations.grpcio import (
        inject, DishkaInterceptor, GrpcioProvider,
    )

2. Create provider. You can use ``grpc.ServicerContext`` as a factory parameter to access request context in ``SESSION`` or ``REQUEST`` scopes.
Use ``google.protobuf.message.Message`` to access certain message in ``REQUEST`` scope.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, message: Message) -> X:
             ...

3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]`` and decorate them using ``@inject``

.. code-block:: python

    class ExampleService(ExampleServiceServicer):
        @inject
        def MyMethod(
            self,
            request: MyRequest,
            context: ServicerContext,
            service: FromDishka[UUIDService],
        ) -> ResponseMessage:
        ...

4. *(optional)* Use ``GrpcioProvider()`` when creating container if you are going to use ``grpc.ServicerContext`` or incoming ``google.protobuf.message.Message`` in providers.

.. code-block:: python

    container = make_container(YourProvider(), GrpcioProvider())

4. Setup dishka interceptors when creating a server. Use ``DishkaInterceptor`` for sync services and ``DishkaAioInterceptor``

.. code-block:: python

    server = make_server(
        ThreadPoolExecutor(max_workers=10),
        interceptors=[
            DishkaInterceptor(container),
        ],
    )


Streaming
************************************

If we receive single request from user like in ``unary_unary`` or ``unary_stream`` methods,
we operate only 2 scopes: ``APP`` and ``REQUEST``.

``stream_unary`` and ``stream_streeam`` methods are different: for one application you have multiple connections (one per client) and each connection delivers multiple messages. To support this we use additional scope: ``SESSION``:

    ``APP`` |rarr| ``SESSION`` |rarr| ``REQUEST``

So, the difference is that if you can share dependencies across all messages within the same stream by declaring them on ``SESSION`` scope. The rest of the logic is the same.