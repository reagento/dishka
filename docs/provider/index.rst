Provider
****************

**Provider** is an object which members are used to construct dependencies. Providers are needed for container to create dependencies.

To create your own provider you inherit from ``Provider`` class and instantiate it when creating a container:

.. code-block:: python

    class MyProvider(Provider):
        pass

    with make_container(MyProvider()) as container:
        pass

You can also set default scope for factories within provider. It will affect only those factories which have no scope set explicitly.

* Inside class:

.. code-block:: python

    class MyProvider(Provider):
        scope=Scope.APP

* Or when instantiating it. This can be also useful for tests to override provider scope.

.. code-block:: python

    with make_container(MyProvider(scope=Scope.APP)) as container:
        pass

Though it is a normal object, not all attributes are analyzed by ``Container``, but only those which are marked with special functions:

.. toctree::

   provide
   alias
   decorate
