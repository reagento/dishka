Quickstart
********************

1. **Install dishka**

.. code-block:: shell

    pip install dishka

2. **Define classes with type hints.** Let's have the ``Service`` class (business logic) that has
two infrastructure dependencies: ``APIClient`` and ``DBGateway``.
``DBGateway`` has its own dependency - ``sqlite3.Connection``.

We want to create an ``APIClient`` instance once during the application's lifetime
and create ``DBGateway`` instances on every request (event) our application handles.

.. literalinclude:: /quickstart/quickstart_example_2.py
   :language: python

3. **Create providers** and specify how to provide dependencies.

Providers are used to set up factories for your objects. To learn more about providers, see :ref:`provider`.

Use ``Scope.APP`` for dependencies that should be created once for the entire application lifetime,
and ``Scope.REQUEST`` for those that should be created for each request, event, etc.
To learn more about scopes, see :ref:`scopes`.

.. literalinclude:: /quickstart/quickstart_example_3_1.py
   :language: python

For the ``Connection`` dependency, we want to make it releasable; thus, we need a custom ``Provider``.

.. literalinclude:: /quickstart/quickstart_example_3_2.py
   :language: python

4. **Create a container**, passing providers.

Containers hold a cache of dependencies and are used to retrieve them.
To learn more about containers, see :ref:`container`.

.. literalinclude:: /quickstart/quickstart_example_4.py
   :language: python

5. **Access dependencies using the container.** Use the ``.get()`` method to access *APP*-scoped dependencies.

.. literalinclude:: /quickstart/quickstart_example_5_1.py
   :language: python

To access the *REQUEST* scope and its dependencies, use a context manager.

.. literalinclude:: /quickstart/quickstart_example_5_2.py
   :language: python

6. **Close the container** when done.

.. literalinclude:: /quickstart/quickstart_example_6.py
   :language: python

.. dropdown:: Full example

   .. literalinclude:: /quickstart/quickstart_example_full.py
      :language: python

7. **(Optional) Integrate with your framework.** If you are using a supported framework, add decorators and middleware for it.
   For more details, see :ref:`integrations`.

.. literalinclude:: /quickstart/quickstart_example_7.py
   :language: python
