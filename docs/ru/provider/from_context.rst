.. _ru-from-context:

from_context
****************

Вы можете вручную добавить некоторые данные при входе в область видимости (scope) и использовать их в фабриках провайдеров. Чтобы это работало, нужно пометить зависимость как получаемую из контекста с помощью ``from_context``, а затем использовать её как обычно. После этого укажите аргумент ``context=`` при входе в соответствующую область видимости.

.. code-block:: python

    from dishka import from_context, Provider, provide, Scope

    class MyProvider(Provider):
        scope = Scope.REQUEST

        app = from_context(provides=App, scope=Scope.APP)
        request = from_context(provides=RequestClass)

        @provide
        def get_a(self, request: RequestClass, app: App) -> A:
            ...

    container = make_container(MyProvider(), context={App: app})
    with container(context={RequestClass: request_instance}) as request_container:
        pass


Хотите переопределить фабрику с ``from_context``? Для этого укажите параметр ``override=True``. Это можно проверить, передав соответствующие ``validation_settings`` при создании контейнера.

.. code-block:: python

    from dishka import provide, from_context, Provider, Scope, make_container
    class MyProvider(Provider):
        scope=Scope.APP

        @provide
        def get_int(self) -> int:
            return 1

        a_override = from_context(provides=int, override=True)

    container = make_container(MyProvider(), context={int: 2})
    a = container.get(int)  # 2
