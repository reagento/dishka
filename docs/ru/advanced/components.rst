.. _ru-components:

Изоляция компонентов и провайдеров
****************************************

Определение проблемы
===========================

Как известно, контейнер может создаваться из нескольких провайдеров, которые динамически связываются вместе. Это позволяет повторно использовать их или частично переопределять в тестах. Такой подход хорошо работает, когда все предоставляемые объекты имеют разные типы. Но что, если есть пересечения? Рассмотрим три ситуации:

1. Только несколько типов используются с разным смыслом в монолитном приложении.
Например, когда есть несколько пулов потоков для разных задач или несколько подключений к разным базам данных. Несмотря на их особое назначение, их различают, создавая новые типы.
2. Несколько частей приложения разрабатываются более или менее независимо, но используются в одном контексте выполнения.
3. У вас модульное приложение с несколькими ограниченными контекстами.

*Первая ситуация* может возникнуть, например, если у вас есть несколько пулов потоков для разных задач или несколько подключений к разным базам данных. Хотя они имеют особое значение, их различают, создавая новые типы.

.. code-block:: python

    from typing import NewType

    MainDbConnection = NewType("MainDbConnection", Connection)

Как только у вас появляются разные типы, Dishka теперь может определять, какой из них используется в каждом конкретном месте.

В *третьей ситуации* у вас, по сути, есть мини-приложения внутри более крупного, со своими собственными областями видимости (scopes) и жизненным циклом событий. В этом случае просто создайте несколько контейнеров.

Отличие возникает, когда у вас есть множество разных типов, и вы не хотите (или даже не можете) заменять их новыми типами, как в пункте 1. Для такого случая у нас есть другое понятие — **компоненты**.

Компонент (Component)
=============================

**Компонент** — это изолированная группа провайдеров в одном контейнере, идентифицируемая строкой. Всегда существует компонент по умолчанию (``DEFAULT_COMPONENT=""``).

Компонент **задается для всего провайдера целиком**, но один провайдер может использоваться в нескольких компонентах с помощью метода ``.to_component(name)``.

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

Компоненты **изолированы**: провайдер не может неявно запрашивать объект из другого компонента. В следующем коде ``MainProvider.foo`` запрашивает целочисленное значение, которое предоставляется только в отдельном компоненте. В данном коде есть ошибка в графе зависимостей, поэтому мы отключим проверку, чтобы продемонстрировать поведение во время выполнения:

.. code-block:: python

    from dishka import make_container, Provider, provide, Scope

    class MainProvider(Provider):
        # default component is used here

        @provide(scope=Scope.APP)
        def foo(self, a: int) -> float:
            return a/10


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

Если один и тот же тип указан в нескольких компонентах, то поиск происходит только в том же компоненте, что и зависимость, если только он не объявлен явно.

Компоненты могут **ссылаться друг на друга**: каждый провайдер может указать имя компонента при объявлении зависимости с помощью аннотации типа ``FromComponent``.

.. code-block:: python

    from typing import Annotated
    from dishka import FromComponent, make_container, Provider, provide, Scope

    class MainProvider(Provider):

        @provide(scope=Scope.APP)
        def foo(self, a: Annotated[int, FromComponent("X")]) -> float:
            return a/10


    class AdditionalProvider(Provider):
        component = "X"

        @provide(scope=Scope.APP)
        def foo(self) -> int:
            return 1

    container = make_container(MainProvider(), AdditionalProvider())
    container.get(float)  # returns 0.1

Теперь ``alias`` можно использовать между компонентами без изменения типа:

.. code-block:: python

    a = alias(int, component="X")


.. note::
    В интеграциях с фреймворками ``FromDishka[T]`` используется для получения объекта из компонента по умолчанию. Чтобы использовать другой компонент, можно применить тот же синтаксис с аннотацией ``Annotated[T, FromComponent("X")]``.