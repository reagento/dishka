.. _from-context:

from_context
****************

You can put some data manually when entering scope and rely on it in your provider factories. To make it work you need to mark a dependency as retrieved from context using ``from_context`` and then use it as usual. Later, set ``context=`` argument when you enter corresponding scope.


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


Do you want to override factory with ``from_context``? To do this, specify the parameter ``override=True``. This can be checked when passing proper ``validation_settings`` when creating container.

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
