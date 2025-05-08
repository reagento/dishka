.. _adding_new:

Adding new integrations
===========================

Though there are some integrations in library you are not limited to use them.

The main points are:

1. Find a way to pass a global container instance. Often it is attached to application instance or passed by a middleware.
2. Find a place to enter and exit request scope and how to pass the container to a handler. Usually, it is entered in a middleware and container is stored in some kind of request context. 

   Alternatively, you can use the ``wrap_injection`` function with ``manage_scope=True`` to automate entering and exiting the request scope without relying on middleware. When enabled, ``manage_scope`` ensures that the container passed to ``wrap_injection`` enters and exits the next scope.

   When you use ``manage_scope=True``, you can pass ``provide_context`` function that allows to populate the container context with passed arguments. This is useful when you want to pass the function scoped arguments to other dependencies without relying on middleware.
   ... code-block:: python

       from dishka import wrap_injection, Provider, provide

       ...
       class AppProvider(Provider):
           request = from_context(provides=Request, scope=Scope.REQUEST)

          @provide(scope=Scope.REQUEST)
          def request(self, request: FromDishka[Request]) -> Iterable[User]:
              yield get_user_from_request(request)

       ...
       wrapped_func = wrap_injection(
           func=func,
           is_async=False,
           manage_scope=True,
           provide_context=lambda req: Request: {Request: req},
        )

3. Configure a decorator. The main option here is to provide a way for retrieving container. Often, need to modify handler signature adding additional parameters. It is also available.
4. Check if you can apply decorator automatically.

While writing middlewares and working with scopes is done by your custom code, we have a helper for creating ``@inject`` decorators - a ``wrap_injection`` function.

* ``container_getter`` is a function with two params ``(args, kwargs)`` which is called to get a container used to retrieve dependencies within scope.
* ``additional_params`` is a list of ``inspect.Parameter`` which should be added to handler signature.

For more details, check existing integrations.
