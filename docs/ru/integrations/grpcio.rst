.. include:: <isonum.txt>

.. _ru-grpcio:

gRPC
============================

Хотя это и не обязательно, вы можете использовать интеграцию ``dishka-grpcio``. Она предоставляет:

* автоматическое управление областями видимости (scope) *REQUEST* и *SESSION* с помощью интерцепторов
* передачу объектов ``Message`` и ``ServicerContext`` как контекстных данных в провайдеры для **унарных (unary)** и **потоковых (stream)** запросов
* внедрение зависимостей в функции-обработчики с помощью декораторов

Поддерживаются grpc и grpc.aio сервисы.

Как использовать
********************

1. Импорт

.. code-block:: python

    from dishka.integrations.grpcio import (
        inject, DishkaInterceptor, GrpcioProvider,
    )

2. Создайте провайдер. Вы можете использовать ``grpc.ServicerContext`` как параметр фабрики для доступа к контексту запроса в областях ``SESSION`` или ``REQUEST``.
Используйте ``google.protobuf.message.Message`` для доступа к конкретному сообщению в области ``REQUEST``.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, message: Message) -> X:
             ...

3. Пометьте параметры ваших обработчиков, которые должны быть внедрены, с помощью ``FromDishka[]`` и декорируйте их с помощью ``@inject``

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

4. *(опционально)* Используйте ``GrpcioProvider()`` при создании контейнера, если вы планируете использовать ``grpc.ServicerContext`` или входящее ``google.protobuf.message.Message`` в провайдерах.

.. code-block:: python

    container = make_container(YourProvider(), GrpcioProvider())

5. Настройте интерцепторы ``dishka`` при создании сервера. Используйте ``DishkaInterceptor`` для синхронных сервисов и ``DishkaAioInterceptor`` для асинхронных.

.. code-block:: python

    server = make_server(
        ThreadPoolExecutor(max_workers=10),
        interceptors=[
            DishkaInterceptor(container),
        ],
    )


Потоковая обработка (Streaming)
************************************

Если мы получаем единичный запрос от пользователя, как в методах ``unary_unary`` или ``unary_stream``,
мы работаем только с 2 областями видимости: ``APP`` и ``REQUEST``.

Методы ``stream_unary`` и ``stream_stream`` отличаются: для одного приложения у вас множество соединений (по одному на клиента) и каждое соединение доставляет множество сообщений. Для поддержки этого мы используем дополнительную область видимости: ``SESSION``:

    ``APP`` |rarr| ``SESSION`` |rarr| ``REQUEST``

Таким образом, разница в том, что вы можете разделять зависимости между всеми сообщениями в рамках одного потока, объявляя их в области ``SESSION``. Остальная логика остается той же.