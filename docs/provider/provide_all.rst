.. _provide_all:

provide_all
******************

``provide_all`` is a helper function which can be used instead of repeating ``provide`` call with just class passed and same scope

These two providers are equal for the container

.. code-block:: python

    from dishka import provide, provide_all, Provider, Scope

    class OneByOne(Provider):
        scope = Scope.APP

        a = provide(ClassA)
        b = provide(ClassB)

    class AllAtOnce(Provider):
        scope = Scope.APP

        ab = provide_all(ClassA, ClassB)


It is also available as a method:

.. code-block:: python

    provider = Provider(scope=Scope.APP)
    provider.provide_all(ClassA, ClassB)

You can combine different ``provide``, ``alias``, ``decorate``, ``from_context``, ``provide_all``, ``from_context`` and others with each other without thinking about the variable names for each of them.

These two providers are equal for the container

.. code-block:: python

    from dishka import alias, decorate, provide, provide_all, Provider, Scope

    class OneByOne(Provider):
        scope = Scope.APP

        data = from_context(Data)
        a = provide(A, provides=AProtocol)
        b = provide(B, providesAProtocol)
        b_alias = alias(source=C, provides=B)
        c_decorate = decorate(CDecorator, provides=C)

    class AllAtOnce(Provider):
        scope = Scope.APP

        provides = (
            provide(A, provides=AProtocol)
            + provide(B, provides=AProtocol)
            + alias(source=C, provides=B)
            + decorate(CDecorator, provides=C)
            + from_context(Data)
        )