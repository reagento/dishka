.. include:: <isonum.txt>

Key concepts
*****************

Dishka is a DI-framework and it is designed to create complex objects following dependency injection principle.
Let's start with some terms.

Dependency
==================

**Dependency** is what you need for some parts of your code to work.
If your *database gateway* needs *database connection* to execute SQL queries, then the connection is a dependency for a gateway.
If your business logic class requires *database gateway* or some *api client* then *api client* and *database gateway* are dependencies for a business logic.
Here, the ``Client`` is a dependency, while ``Service`` is a dependant.

.. code-block:: python

    class Service:
        def __init__(self, client: Client):
            self.client = client

So, dependency is just an object required by another object. Dependencies can depend on other objects, which are their dependencies.

To follow dependency injection rule, dependent objects should receive their dependencies and not request them themselves.
The same classes can be instantiated with different values of their dependencies.
At least in tests.


Scope
===========

**Scope** is a lifespan of a dependency.
Some dependencies live for the entire application lifetime, while others are created and destroyed with each request.
In more rare cases, you need more short-lived objects.
You set a scope for each dependency when you configure how it is created.

Standard scopes are (with some skipped):

    ``APP`` |rarr| ``REQUEST`` |rarr| ``ACTION`` |rarr| ``STEP``

You decide when to enter and exit each scope, but this is done one by one.
If you enter the ``APP`` scope, then the next step deeper is to enter the ``REQUEST`` scope.

.. note::
    ``APP`` scope can be used for lazy initialization of singletons, while ``REQUEST`` scope is good for processing events like HTTP requests or messenger updates. It is unlikely that you will need other scopes


In Dishka dependencies are lazy — they are created when you first request them.
If the same dependency is requested multiple times within a single scope, then the same instance is returned (you can disable it for each dependency separately).
A created dependency is kept until you exit the scope.
And at that moment, it is not just dropped away, but the corresponding finalization steps are done.
You can enter same scope multiple times concurrently so that to have multiple instances of objects you can work with simultaneously.

Each object can depend on other objects from the same or previous scopes.
So, if you have ``Config`` with scope of *APP* and ``Connection`` with scope of *REQUEST*,
you cannot have *APP*-scoped object which requires a connection,
but you can have *REQUEST*-scoped object which requires a ``Connection`` or a ``Config`` (or even both).

For a web application, enter ``APP`` scope on startup and ``REQUEST`` scope for each HTTP request.

You can create a custom scope by defining your own ``Scope`` class if the standard scope flow doesn't fit your needs.

:ref:`Read more about custom and skipped scopes<scopes>`

Container
==================

**Container** is an object you use to get your dependencies.

You simply call ``.get(SomeType)`` and it finds a way to provide you with an instance of that type.
Container itself doesn't create objects but manages their lifecycle and caches.
It delegates object creation to providers that are passed during creation.

Each container is assigned to a certain scope. To enter a nested scope, you call it and use it as a context manager.
According to the scope order, container can be used to get dependencies from its own and previous scopes.

.. code-block:: python

    app_container = make_container(provider1, provider2)  # enter APP scope

    config = app_container.get(Config)  # APP-scoped object

    with container() as request_container:  # enter REQUEST scope
        connection = request_container.get(Connection)  # REQUEST-scoped object
        config = request_container.get(Config)  # APP-scoped object

Async container works in the same manner, but you should use async context manager and await the result of ``.get``.

Some containers are concurrently safe, others are not: this is configured when you call a context manager.
For web applications, it is good to have APP-scoped container thread/task-safe, but REQUEST-scoped containers do not require it, and this is the default behavior.


:ref:`Read more about container API<container>`

Provider
===============

**Provider** is an object which members are used to construct dependencies.
It is a normal object, but some attributes must be marked with special decorators so they will be used by a container.
To create your own provider, you inherit from ``Provider`` class and instantiate it when creating a container:

.. code-block:: python

    class MyProvider(Provider):
        pass

    container = make_container(MyProvider())


There are 4 special functions:

* ``@provide`` is used to declare a factory providing a dependency. It can be used with some class or as a method decorator. :ref:`Read more<provide>`
* ``alias`` is used to allow retrieving the same object by different type hints. :ref:`Read more<alias>`
* ``from_context`` is used to mark a dependency as context data, which will be set manually when entering a scope. :ref:`Read more<from-context>`
* ``@decorate`` is used to modify or wrap an object which is already configured in another ``Provider``. :ref:`Read more<decorate>`

Component
====================
**Component** is an isolated group of providers within the same container, identified by a unique string.
When a dependency is requested, it is only searched within the same component as its direct dependant, unless explicitly
specified otherwise.

This structure allows you to build different parts of the application separately without worrying about using the same
types.

.. code-block:: python

    class MainProvider(Provider):

        @provide(scope=Scope.APP)
        def foo(self, a: Annotated[int, FromComponent("X")]) -> float:
            return a/10

        @provide(scope=Scope.APP)
        def bar(self, a: int) -> complex:
            return a + 0j


    class AdditionalProvider(Provider):
        component = "X"

        @provide(scope=Scope.APP)
        def foo(self) -> int:
            return 1


    container = make_container(MainProvider(), AdditionalProvider())
    container.get(float)  # returns 0.1
    container.get(complex)  # raises NoFactoryError

:ref:`Read more about components management<components>`