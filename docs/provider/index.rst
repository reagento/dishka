Provider
****************

**Provider** is an object which members are used to construct dependencies. ``Provider`` contains different factories and other entities and then is used to create a ``Container``. You can have multiple providers in one application and combine them in different ways to make it more modular.

To configure provider you can either inherit and use decorators on you methods or just create an instance and use its methods.

For example, imagine you have two classes: connection which is retrieved from external library and a gateway which requires such a connection.

.. code-block:: python

    class Connection:
        pass

    class Gateway:
        def __init__(self, conn: Connection):
            pass

You can configure ``Provider`` with code like this:

.. code-block:: python

    from dishka import make_container, Provider, Scope

    def get_connection() -> Iterable[Connection]:
        conn = connect(uri)
        yield conn
        conn.close()

    provider = Provider(scope=Scope.APP)
    provider.provide(get_connection)
    provider.provide(Gateway)

    with make_container(provider) as container:
        ...

Or using inheritance:

.. code-block:: python

    from dishka import make_container, Provider, provide, Scope

    class MyProvider(Provider):
        @provide
        def get_connection(self) -> Iterable[Connection]:
            conn = connect(uri)
            yield conn
            conn.close()

        gateway = provider.provide(Gateway)

    with make_container(MyProvider(scope=Scope.APP)) as container:
        pass

You class-based provider can have ``__init__`` method and methods access ``self`` as usual. It can be useful for passing configuration:

.. code-block:: python

    class MyProvider(Provider):
        def __init__(self, uri: str, scope: Scope):
            super().__init__(scope=scope)  # do not forget `super`
            self.uri = uri

        @provide
        def get_connection(self) -> Iterable[Connection]:
            conn = connect(self.uri)  #
            yield conn
            conn.close()

        gateway = provide(Gateway)

    provider = MyProvider(uri=os.getenv("DB_URI"), scope=Scope.APP)
    with make_container(provider) as container:
        pass


Dependencies have scope and there are three places to set it (according to their priority):

* When registering single factory passing to ``provide`` method

.. code-block:: python

    class MyProvider(Provider):
        gateway = provide(Gateway, scope=Scope.APP)

* When instantiating provider:

.. code-block:: python

    provider = Provider(scope=Scope.APP)

* Inside class:

.. code-block:: python

    class MyProvider(Provider):
        scope=Scope.APP

Though it is a normal object, not all attributes are analyzed by ``Container``, but only those which are marked with special functions:

.. toctree::

   provide
   alias
   decorate
