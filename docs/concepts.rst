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
Some dependencies can live while application is running, others are created and destroyed on each request. In more rare cases you need more short-lived objects. You set a scope for your dependency when you configure how to create it.

Standard scopes are (excluding skipped):

    ``APP`` |rarr| ``REQUEST`` |rarr| ``ACTION`` |rarr| ``STEP``

You decide when to enter and exit them, but it is done one by one. If you entered ``APP`` scope then the next step deeper will enter ``REQUEST`` scope.

.. note::
    ``APP`` scope can be used for lazy initialization of singletons, while ``REQUEST`` scope is good for processing events like HTTP-requests or messenger updates. It is unlikely that you will need other scopes


In dishka dependencies are lazy - they are created when you first request them. If the same dependency is requested multiple times within one scope then the same instance is returned (you can disable it for each dependency separately). A created dependency is kept until you exit the scope. And in that moment it is not just dropped away, but corresponding finalization steps are done. You can enter same scope multiple times concurrently so to have multiple instances of objects you can work simultaneously.

Each object can depend on other objects from the same or previous scopes. So, if you have ``Config`` with scope of *APP* and ``Connection`` with scope of *REQUEST* you cannot have an *APP*-scoped object which requires a connection, but you can have *REQUEST*-scoped object which requires a ``Connection`` or a ``Config`` (or even both).

If you are developing web application, you would enter ``APP`` scope on startup, and you would ``REQUEST`` scope in each HTTP-request.

You can provide your own Scopes class if you are not satisfied with standard flow.

:ref:`Read more about custom and hidden scopes<scopes>`

Container
==================

**Container** is an object you use to get your dependency.

You just call ``container.get(SomeType)`` and it finds a way to get you an instance of that type. It does not create things itself, but manages their lifecycle and caches. It delegates objects creation to providers which are passed during creation.

Each container is assigned to a certain scope. To enter the nested scope you call it and use as a context manager.
According to scopes order container can be used to get dependencies from its and previous scopes.

.. code-block:: python

    app_container = make_container(provider1, provider2)  # enter APP scope

    config = app_container.get(Config)  # APP-scoped object

    with container() as request_container:  # enter REQUEST scope
        connection = request_container.get(Connection)  # REQUEST-scoped object
        config = request_container.get(Config)  # APP-scoped object

Async container is working in the same manner, but you should use async context manager and await the result of get

Some containers are concurrently safe, others are not: it is configured when you call a context manager. For web applications it is good to have APP-scoped container thread/task-safe, but REQUEST-scoped containers do not it, and it is default behavior.


:ref:`Read more about container API<container>`

Provider
===============

**Provider** is an object which members are used to construct dependencies. It is a normal object, but some attributes must be marked with special decorators so they will be used by a container. To create your own provider you inherit from ``Provider`` class and instantiate it when creating a container:

.. code-block:: python

    class MyProvider(Provider):
        pass

    container = make_container(MyProvider())


There are 3 special functions:

* ``@provide`` is used to declare a factory providing a dependency. It can be used with some class or as a method decorator. :ref:`Read more<provide>`
* ``alias`` is used to allow retrieving of the same object by different type hints. :ref:`Read more<alias>`
* ``from_context`` is used to mark a dependency as context data, which will be set manually when entering a scope. :ref:`Read more<from-context>`
* ``@decorate`` is used to modify or wrap an object which is already configured in another ``Provider``. :ref:`Read more<decorate>`

Component
====================
**Component** - is an isolated group of providers within the same container identified by a string. When dependency is requested it is searched only within the same component as its dependant, unless it is declared explicitly.

This allows you to have multiple parts of application build separately without need to think if they use same types.

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