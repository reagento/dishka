Context data
====================

Often, your scopes are assigned with some external events: HTTP-requests, message from queue, callbacks from framework. You can use those objects when creating dependencies.

The difference from normal factories is that they are not created inside some ``Provider``, but passed to the scope.

Working with context data consists of three parts:

1. Declaration that object is received from context using :ref:`from-context`. You need to provide the type and scope.
    * For the context passed to ``make_container`` and ``make_async_container`` functions it is done automatically in default component.
    * Context is shared across all providers. You do not need to specify it in each provider.
    * For the frameworks integrations you can use predefined providers instead of defining context data manually
    * To access context from additional components you need to use ``from_context`` is each of them
2. Usage of that object in providers.
3. Passing actual values on scope entrance. It can be container creation for top level scope or container calls for nested ones. Use it in form ``context={Type: value,...}``.

.. code-block:: python

    from framework import Request
    from dishka import Provider, make_container, Scope, from_context, provide


    class MyProvider(Provider):
        scope = Scope.REQUEST

        # declare context data for nested scope
        request = from_context(provides=Request, scope=Scope.REQUEST)

        # use objects as usual
        @provide
        def a(self, request: Request, broker: Broker) -> A:
            return A(data=request.contents)

    # passed APP-scoped context variable is automatically available as a dependency
    container = make_container(MyProvider(), context={Broker: broker})

    while True:
        request = broker.recv()
        # provide REQUEST-scoped context variable
        with container(context={Request: request}) as request_container:
            a = request_container.get(A)

.. note::

    If you are using *multiple components*, you need to specify ``from_context`` in them separately though the context is shared. Context data is always stored in default component, so, other components may not use it and have factories instead.
