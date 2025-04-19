Контекстные данные
====================

Часто ваши области видимости (scopes) связаны с внешними событиями: HTTP-запросами, сообщениями из очереди, колбэками от фреймворка. Вы можете использовать эти объекты при создании зависимостей.

Отличие от обычных фабрик заключается в том, что они создаются не внутри какого-либо ``Provider``, а передаются в область видимости.

Работа с контекстными данными состоит из трёх частей:

1. Объявление, что объект получен из контекста, с помощью :ref:`from-context`. Необходимо указать тип и область видимости.
2. Использование этого объекта в провайдерах.
3. Передача фактических значений при входе в область видимости. Это может быть создание контейнера для верхнего уровня или вызовы контейнера для вложенных областей. Используйте это в формате ``context={Type: value, ...}``.

.. code-block:: python

    from framework import Request
    from dishka import Provider, make_container, Scope, from_context, provide


    class MyProvider(Provider):
        scope = Scope.REQUEST

        # declare source
        request = from_context(provides=Request, scope=Scope.REQUEST)
        event_broker = from_context(provides=Broker, scope=Scope.APP)

        # use objects as usual
        @provide
        def a(self, request: Request, broker: Broker) -> A:
            return A(data=request.contents)

    # provide APP-scoped context variable
    container = make_container(MyProvider(), context={Broker: broker})

    while True:
        request = broker.recv()
        # provide REQUEST-scoped context variable
        with container(context={Request: request}) as request_container:
            a = request_container.get(A)

.. note::
    Если вы используете *несколько компонентов*, вам нужно указать ``from_context`` в каждом из них отдельно, даже если контекст общий. Данные контекста всегда хранятся в компоненте по умолчанию, поэтому другие компоненты могут не иметь к ним доступа и вместо этого используют фабрики.