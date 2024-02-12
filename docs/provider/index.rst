Provider
****************

**Provider** is an object which members are used to construct dependencies. Providers are needed for container to create dependencies.

To create your own provider you inherit from ``Provider`` class and instantiate it when creating a container:

.. code-block:: python

    class MyProvider(Provider):
        pass

    with make_container(MyProvider()) as container:
        pass


Though it is a normal object, not all attributes are analyzed by ``Container``, but only those which are marked with special funcions:

.. toctree::

   provide
   alias
   decorate
