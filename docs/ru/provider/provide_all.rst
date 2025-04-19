.. _ru-provide_all:

provide_all
******************

Функция ``provide_all`` — это вспомогательная функция, которая может использоваться вместо повторяющихся вызовов ``provide`` с передачей только класса и того же скоупа.

Эти два провайдера эквивалентны для контейнера.

.. code-block:: python

    from dishka import provide, provide_all, Provider, Scope

    class OneByOne(Provider):
        scope = Scope.APP

        a = provide(ClassA)
        b = provide(ClassB)

    class AllAtOnce(Provider):
        scope = Scope.APP

        ab = provide_all(ClassA, ClassB)


Это также доступно как метод:

.. code-block:: python

    provider = Provider(scope=Scope.APP)
    provider.provide_all(ClassA, ClassB)

Вы можете комбинировать различные ``provide``, ``alias``, ``decorate``, ``from_context``, ``provide_all``, ``from_context`` и другие методы друг с другом, не задумываясь о названиях переменных для каждого из них.

Эти два провайдера равнозначны для контейнера.

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