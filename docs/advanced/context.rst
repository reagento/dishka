Context data
====================

Often, your scopes are assigned with some external events: HTTP-requests, message from queue, callbacks from framework. You can use those objects when creating dependencies.

The difference from normal factories is that they are not created inside some ``Provider``, but passed to the scope.

Working with context data consists of three parts:

1. Declaration that object is received from context using :ref:`from-context`. You need to provide the type and scope.
2. Usage of that object in providers. There is now difference how the object is
3. Passing actual values on scope entrance. It can be container creation for top level scope or container calls for nested ones. Use it in form ``context={Type: value,...}``

.. code-block:: python

    from framework import Request

    class MyProvider:
        scope=Scope.REQUEST

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
        with container(context={Request:request}) as request_container:
             a = request_container.get(A)

.. note::

    If your are using *multiple components*, you need to specify ``from_context`` in them separately though the context is shared. Context data is always stored in default component, so, other components may not use it and have factories instead.