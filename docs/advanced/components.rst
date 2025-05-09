.. _components:

Components and providers isolation
****************************************

Problem definition
===========================

As you know, container can be created from multiple providers,
which are dynamically bound together. It allows you to reuse them
or partially override in tests. It works well while you have different types
across all provided objects. But what if there are some intersections.
Let's talk about three situations:

1. Only several types are used with different meaning within a monolithic app.
2. Several parts of an application are developed them more or less independently, while they are used within same processing context.
3. You have a modular application with multiple bounded contexts.

**First situation** can appear when you have for-example multiple thread pools
for different tasks or multiple database connections for different databases.
While they have special meaning you distinguish them by creating new types

.. code-block:: python

    from typing import NewType

    MainDbConnection = NewType("MainDbConnection", Connection)

Once you have different types dishka can now understand which one is used
in each place.

In the **third situation** you actually have mini-applications inside
a bigger one with their own scopes and event lifecycle. So just create multiple
containers.

The different thing is when you have a bunch of different types and you do not
want or even cannot replace them with new types as in p.1. For this case
we have a different concept - **components**.


Component
==============
**Component** - is an isolated group of providers within the same container
identified by a string. There is always a default component (``DEFAULT_COMPONENT=""``).

Component is **set for the whole provider**, but single provider can be used
in multiple components using ``.to_component(name)``.

.. code-block:: python

    from dishka import make_container, Provider

    # default component is used when not specified
    provider0 = Provider()

    class MyProvider(Provider):
        # component can be set in class
        component = "component_name"

    provider1 = MyProvider()

    # component can be set on instance creation
    provider2 = MyProvider(component="other")

    # same provider instance is casted to use with different component
    provider3 = provider2.to_component("additional")

    container = make_container(provider0, provider1, provider2, provider3)

Components are **isolated**: provider cannot implicitly request an object
from another component:

.. code-block:: python

    from dishka import Provider, Scope, make_container, provide

    class DBConnection(Protocol): ...
    class UserDBConnection(DBConnection): ...
    class CommentDBConnection(DBConnection): ...
    # we might use different databases for users and comments,
    # although the interface for communication will remain common

    class UserDAO:
        def __init__(self, db: DBConnection): ...
        # we need to distinguish this DBConnection ...

    class CommentDAO:
        def __init__(self, db: DBConnection): ...
        # ... from this DBConnection

    class UserProvider(Provider):
        component = "user"
        scope = Scope.APP  # should be REQUEST, but set to APP for the sake of simplicity
        db_connection = provide(UserDBConnection, provides=DBConnection)
        dao = provide(UserDAO)

    class CommentProvider(Provider):
        component = "comment"
        scope = Scope.APP  # should be REQUEST, but set to APP for the sake of simplicity
        db_connection = provide(CommentDBConnection, provides=DBConnection)
        dao = provide(CommentDAO)

    container = make_container(UserProvider(), CommentProvider())
    container.get(DBConnection, component="user")  # UserDBConnection
    container.get(DBConnection, component="comment")  # CommentDBConnection


In the following code ``MainProvider.foo`` requests
integer value which is only provided in separate component. In the code below
there is an error in dependency graph, so we will disable validation to show
runtime behavior:

.. code-block:: python

    from dishka import make_container, Provider, provide, Scope

    class MainProvider(Provider):
        # default component is used here

        @provide(scope=Scope.APP)
        def foo(self, a: int) -> float:
            return a / 10


    class AdditionalProvider(Provider):
        component = "X"

        @provide(scope=Scope.APP)
        def foo(self) -> int:
            return 1

    # we will get error immediately during container creation, skip validation for demo needs
    container = make_container(MainProvider(), AdditionalProvider(), skip_validation=True)
    # retrieve from component "X"
    container.get(int, component="X")  # value 1 would be returned
    # retrieve from default component
    container.get(float)  # raises NoFactoryError because int is in another component


If the same type is provided in multiple components, it is searched only within
the same component as its dependant, unless it is declared explicitly.

Components can **link to each other**: each provider can add a component name
when declaring a dependency by ``FromComponent`` type annotation.


.. code-block:: python

    from typing import Annotated
    from dishka import FromComponent, make_container, Provider, provide, Scope

    class MainProvider(Provider):

        @provide(scope=Scope.APP)
        def foo(self, a: Annotated[int, FromComponent("X")]) -> float:
            return a / 10


    class AdditionalProvider(Provider):
        component = "X"

        @provide(scope=Scope.APP)
        def foo(self) -> int:
            return 1

    container = make_container(MainProvider(), AdditionalProvider())
    container.get(float)  # returns 0.1


``alias`` now can be used across components without changing the type:

.. code-block:: python

    a = alias(int, component="X")


.. note::
    In frameworks integrations ``FromDishka[T]`` is used to get an object
    from default component. To use other component you can use the same syntax
    with annotated ``Annotated[T, FromComponent("X")]``.

