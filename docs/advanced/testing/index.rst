Testing with dishka
***************************

Testing your code does not always require the whole application to be started. You can have unit tests for separate components and even integration tests which check only specific links. In many cases you do not need IoC-container: you create objects with a power of **Dependency Injection** and not framework.

For other cases which require calling functions located on application boundaries you need a container. These cases include testing your view functions with mocks of business logic and testing the application as a whole. Comparing to a production mode you will still have same implementations for some classes and others will be replaced with mocks. Luckily, in ``dishka`` your container is not an implicit global thing and can be replaced easily.

There are many options to make providers with mock objects. If you are using ``pytest`` then you can

* use fixtures to configure mocks and then pass those objects to a provider
* create mocks in a provider and retrieve them in pytest fixtures from a container

The main limitation here is that a container itself cannot be adjusted after creation. You can configure providers whenever you want before you make a container. Once it is created dependency graph is build and validated, and all you can do is to provide context data when entering a scope.


Example
===================

Imagine, you have a service built with FastAPI:

.. literalinclude:: ./app_before.py

And a container:

.. literalinclude:: ./container_before.py

First of all - split your application factory and container setup.

.. literalinclude:: ./app_factory.py

Create a provider with you mock objects. You can still use production providers and override dependencies in a new one. Or you can build container only with new providers. It depends on the structure of your application and type of a test.

.. literalinclude:: ./fixtures.py

Write tests.

.. literalinclude:: ./sometest.py


Bringing all together
============================


.. literalinclude:: ./test_example.py
