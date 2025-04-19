.. _ru-provide:

provide
******************

Функция ``provide`` используется для объявления фабрики, которая предоставляет зависимость. Её можно использовать с классом или в качестве декоратора метода (как синхронного, так и асинхронного). Она поддерживает финализацию зависимости, если сделать метод генератором.

Объект Provider также имеет метод ``.provide`` с такой же логикой.

Если provide используется с классом, он анализирует аннотации типов в ``__init__``, чтобы определить зависимости. Если применяется к методу, он проверяет аннотации параметров и тип возвращаемого значения. Последний описывает, какой объект создаёт этот метод.

Аргумент ``scope`` обязателен и определяет время жизни создаваемого объекта.
По умолчанию результат кешируется в пределах scope. Это можно отключить, указав ``cache=False``.

* Простой случай: добавьте метод и пометьте его декоратором ``@provide``.

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> A:
            return A()

* Нужна финализация при выходе из scope? Сделайте метод генератором

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> Iterable[A]:
            a = A()
            yield a
            a.close()

Также, если во время обработки процесса (внутри блока ``with``) возникает ошибка, она будет передана в генератор:

.. code-block:: python

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> Iterable[A]:
            a = A()
            exc = yield a
            # exc will be None if an exception has not occurred
            if exc:
                print("Some exception while process handling: ", exc)
            a.close()

* Нет особой логики и нужно просто создать класс через его ``__init__``? Тогда добавьте атрибут provider, используя ``provide`` как функцию, передающую этот класс.

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        a = provide(A, scope=Scope.REQUEST)

* Нужно создать экземпляр дочернего класса, когда запрашивается родительский? Добавьте атрибут ``source`` в функцию ``provide`` с указанием родительского класса, а первым параметром передайте дочерний.

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        a = provide(source=AChild, scope=Scope.REQUEST, provides=A)

* Хотите перейти в ``async``? Сделайте методы provide асинхронными. Создайте асинхронный контейнер. Используйте ``async with`` и await при вызовах ``get``.

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
       @provide(scope=Scope.APP)
       async def get_a(self) -> A:
          return A()

    container = make_async_container(MyProvider())
    a = await container.get(A)

* Надоело указывать ``scope=`` для каждой зависимости? Установите его внутри класса ``Provider``, и все фабрики без явного scope будут использовать его.

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
       scope=Scope.APP

       @provide  # uses provider scope
       async def get_a(self) -> A:
          return A()

       @provide(scope=Scope.REQUEST)  # has own scope
       async def get_b(self) -> B:
          return B()

* Есть несколько интерфейсов, которые могут быть реализованы одним классом? Используйте ``AnyOf`` в качестве аннотации результата.

.. code-block:: python

    from dishka import AnyOf, provide, Provider, Scope

    class MyProvider(Provider):
        scope=Scope.APP

        @provide
        def p(self) -> AnyOf[A, AProtocol]:
            return A()

Это работает аналогично :ref:`alias`.

* Хотите получать зависимости от родительских классов? Используйте ``WithParents`` в качестве хинта для результата:

.. code-block:: python

    from dishka import WithParents, provide, Provider, Scope

    class A(Protocol): ...
    class AImpl(A): ...

    class MyProvider(Provider):
        scope=Scope.APP

        @provide
        def a(self) -> WithParents[AImpl]:
            return A()

    container = make_async_container(MyProvider())
    a = await container.get(A)
    a = await container.get(AImpl)
    a is a # True


WithParents создаёт только одну фабрику и множество алиасов, что эквивалентно ``AnyOf[AImpl, A]``. Следующие родительские классы игнорируются: ``type``, ``object``, ``Enum``, ``ABC``, ``ABCMeta``, ``Generic``, ``Protocol``, ``Exception``, ``BaseException``.

* Зависимости вашего объекта (и их зависимости) могут быть легко созданы путём вызова их конструкторов. Вам не нужно регистрировать их вручную. Используйте ``recursive=True`` для автоматической регистрации.

.. code-block:: python

    class A: ...

    class B:
        def __init__(self, a: A): ...

    class C:
        def __init__(self, b: B): ...

    class MyProvider(Provider):
        c = provide(C, scope=Scope.APP, recursive=True)

* Хотите переопределить фабрику? Для этого укажите параметр ``override=True``. Это можно проверить, передав соответствующие ``validation_settings`` при создании контейнера.

.. code-block:: python

    from dishka import provide, Provider, Scope, make_container

    class MyProvider(Provider):
        scope=Scope.APP

        @provide
        def get_int(self) -> int:
            return 1

        @provide(override=True)
        def get_int2(self) -> int:
            return 2

    container = make_container(MyProvider())
    a = container.get(int)  # 2

* Вы можете использовать фабрику с Generic-классами

.. code-block:: python

    class MyProvider(Provider):
        @provide
        def make_a(self, type_: type[T]) -> A[T]:
            ...

