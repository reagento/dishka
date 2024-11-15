Quickstart
********************

1. **Install Dishka.**

.. code-block:: shell

    pip install dishka

2. **Define your classes with type hints.** Imagine you have two classes: ``Service`` (business logic) and
   ``DAO`` (data access), along with an external API client:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 6-21

3. **Create** ``Provider`` instance and specify how to provide dependencies.

Providers are used only to set up factories providing your objects.

Use ``scope=Scope.APP`` for dependencies created once for the entire application lifetime,
and ``scope=Scope.REQUEST`` for those that need to be recreated for each request, event, etc.
To learn more about scopes, see :ref:`scopes`

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 24-30

To provide a connection, you might need some custom code:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 33-41

4. **Create main** ``Container`` instance, passing providers, and enter ``APP`` scope.

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 44-47

5. **Access dependencies using container.** Container holds a cache of dependencies and is used to retrieve them.
   You can use ``.get`` method to access ``APP``-scoped dependencies:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 49-50

6. **Enter and exit** ``REQUEST`` **scope repeatedly using a context manager**:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 52-60

7. **Close container** when done:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 62

8. **Integrate with your framework.** If you are using a supported framework, add decorators and middleware for it.
   For more details, see :ref:`integrations`

.. code-block:: python

    from dishka.integrations.fastapi import (
        FromDishka, inject, setup_dishka,
    )


    @router.get("/")
    @inject
    async def index(service: FromDishka[Service]) -> str:
        ...


    ...
    setup_dishka(container, app)
