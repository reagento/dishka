Провайдер (Provider)
************************

**Provider (Провайдер)** — это объект, члены которого используются для создания зависимостей. ``Provider`` содержит различные фабрики и другие сущности, а затем применяется для создания ``Container (Контейнера)``. В одном приложении может быть несколько провайдеров, и их можно комбинировать разными способами для повышения модульности.

Для настройки провайдера можно либо унаследовать его и использовать декораторы для методов, либо просто создать экземпляр и работать с его методами.

Например, представим, что у нас есть два класса: соединение (connection), которое получается из внешней библиотеки, и шлюз (gateway), требующий такого соединения.

.. code-block:: python

    class Connection:
        pass

    class Gateway:
        def __init__(self, conn: Connection):
            pass

Вы можете настроить ``Provider`` с помощью такого кода:

.. code-block:: python

    from dishka import make_container, Provider, Scope

    def get_connection() -> Iterable[Connection]:
        conn = connect(uri)
        yield conn
        conn.close()

    provider = Provider(scope=Scope.APP)
    provider.provide(get_connection)
    provider.provide(Gateway)

    container = make_container(provider)


Или использовать наследование:

.. code-block:: python

    from dishka import make_container, Provider, provide, Scope

    class MyProvider(Provider):
        @provide
        def get_connection(self) -> Iterable[Connection]:
            conn = connect(uri)
            yield conn
            conn.close()

        gateway = provide(Gateway)

    container = make_container(MyProvider(scope=Scope.APP))

Ваш классовый провайдер может иметь метод ``__init__`` и другие методы, обращающиеся к ``self`` как обычно. Это может быть полезно для передачи конфигурации:

.. code-block:: python

    class MyProvider(Provider):
        def __init__(self, uri: str, scope: Scope):
            super().__init__(scope=scope)  # do not forget `super`
            self.uri = uri

        @provide
        def get_connection(self) -> Iterable[Connection]:
            conn = connect(self.uri)  # use passed configuration
            yield conn
            conn.close()

        gateway = provide(Gateway)

    provider = MyProvider(uri=os.getenv("DB_URI"), scope=Scope.APP)
    container = make_container(provider)

Зависимости имеют область видимости (scope), и есть три места, где её можно задать (в порядке убывания приоритета):

* При регистрации фабрики — передавая в метод ``provide``

.. code-block:: python

    class MyProvider(Provider):
        gateway = provide(Gateway, scope=Scope.APP)

* При создании провайдера — во время его инициализации

.. code-block:: python

    provider = Provider(scope=Scope.APP)

* Внутри класса (через атрибуты):

.. code-block:: python

    class MyProvider(Provider):
        scope=Scope.APP

.. raw:: html

    <br>


.. warning::

   Провайдер внутри себя определяет атрибуты, такие как ``factories``, ``aliases``, ``decorators`` и ``context_vars``.
   Если переопределить их в подклассе, это нарушит разрешение зависимостей. Используйте другие имена.

    .. code-block:: python

        class MyProvider(Provider):
            scope = ...

            factories = provide(SomeClass)  # ERROR

.. raw:: html

    <br>

Хотя провайдер — это обычный объект, ``Container`` анализирует не все его атрибуты, а только те, которые помечены специальными функциями.

.. toctree::

   provide
   provide_all
   alias
   from_context
   decorate
