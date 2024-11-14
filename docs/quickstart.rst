Quickstart
********************

1. Install dishka

.. code-block:: shell

    pip install dishka

2. Write your classes, fill type hints. Imagine, you have two classes: Service (kind of business logic) and DAO (kind of data access) and some external api client:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 6-21

3. Create Provider instance and setup how to provide dependencies.

Providers are only used to setup all factories providing your objects.

We use ``scope=Scope.APP`` for dependencies which are created only once in application lifetime,
and ``scope=Scope.REQUEST`` for those which should be recreated for each processing request/event/etc.
To read more about scopes, refer :ref:`scopes`

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 24-30

To provide connection we might need to write some custom code:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 33-41

4. Create main ``Container`` instance passing providers, and step into ``APP`` scope.

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 44-47

5. Container holds dependencies cache and is used to retrieve them. Here, you can use ``.get`` method to access APP-scoped dependencies:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 49-50

6. You can enter and exit ``REQUEST`` scope multiple times after that using context manager:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 52-60

7. Close container in the end:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 62

8. If you are using supported framework add decorators and middleware for it.
For more details see :ref:`integrations`

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
