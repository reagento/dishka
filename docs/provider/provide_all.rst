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